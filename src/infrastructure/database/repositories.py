"""Repository truy cập và quản lý vòng đời dữ liệu các đoạn văn bản (Chunks)."""
import json
import threading
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.infrastructure.config import Config
from src.infrastructure.database.models import Chunk

# Đường dẫn tệp cơ sở dữ liệu SQLite trong thư mục data/
DB_PATH = Config.DATA_DIR / "historical_knowledge" / "staging_chunks.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Khởi tạo Engine với timeout chờ khóa SQLite và bộ tuần tự hóa JSON UTF-8
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"timeout": 60},
    json_serializer=lambda obj: json.dumps(
        obj,
        ensure_ascii=False
    )
)

# Khởi tạo Session factory dùng cho toàn bộ phiên làm việc
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ChunkRepository:
    """Repository quản lý hàng đợi và trạng thái trích xuất của các chunk.

    Áp dụng cơ chế khóa hai cấp:
    1. Khóa cấp lớp (Class-level lock): Đồng bộ hóa truy cập giữa các luồng trong cùng tiến trình.
    2. Câu lệnh SQL nguyên tử (Atomic UPDATE ... RETURNING): Ngăn chặn xung đột tranh chấp (Race Condition)
       giữa các tiến trình/terminal độc lập cùng truy cập CSDL SQLite.
    """
    _lock = threading.Lock()

    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self._session_factory = session_factory

    def fetch_pending(self, limit: Optional[int] = None) -> List[Tuple[str, str]]:
        """Lấy danh sách các cặp (chunk_id, text) đang ở trạng thái PENDING.

        Args:
            limit: Giới hạn số lượng bản ghi cần lấy (None nếu lấy tất cả).

        Returns:
            List[Tuple[str, str]]: Danh sách chứa tuple (chunk_id, nội dung văn bản).
        """
        with self._lock:
            with self._session_factory() as session:
                query = (
                    session.query(Chunk)
                    .filter(Chunk.status == "PENDING")
                    .order_by(Chunk.chunk_id)
                )
                if limit:
                    query = query.limit(limit)
                return [
                    (c.chunk_id, c.chunk_overlap_200 or c.text)
                    for c in query.all()
                ]

    def claim_next_pending(self) -> Optional[Tuple[str, str]]:
        """Nhận quyền xử lý nguyên tử (Atomic Task Leasing) 1 chunk PENDING và chuyển sang PROCESSING.

        Returns:
            Optional[Tuple[str, str]]: Tuple (chunk_id, nội dung văn bản) hoặc None nếu hàng đợi rỗng.
        """
        with self._lock:
            with self._session_factory() as session:
                stmt = text(
                    """
                    UPDATE chunk
                    SET status = 'PROCESSING'
                    WHERE chunk_id = (
                        SELECT chunk_id FROM chunk
                        WHERE status = 'PENDING'
                        ORDER BY chunk_id
                        LIMIT 1
                    )
                    RETURNING chunk_id, text, chunk_overlap_200
                    """
                )
                row = session.execute(stmt).fetchone()
                session.commit()
                if not row:
                    return None
                chunk_id, text_val, overlap_val = row
                return (chunk_id, overlap_val or text_val)

    def reset_processing_to_pending(self) -> int:
        """Khôi phục toàn bộ các chunk đang kẹt ở trạng thái PROCESSING về lại PENDING.

        Thường sử dụng để dọn dẹp trạng thái khi tiến trình worker trước đó bị dừng đột ngột.

        Returns:
            int: Số lượng bản ghi đã được khôi phục.
        """
        with self._lock:
            with self._session_factory() as session:
                count = (
                    session.query(Chunk)
                    .filter(Chunk.status == "PROCESSING")
                    .update({"status": "PENDING"})
                )
                session.commit()
                return count

    def update_provider(self, chunk_id: str, provider: str) -> None:
        """Cập nhật thông tin nhà cung cấp (provider) thực hiện trích xuất cho chunk."""
        with self._lock:
            with self._session_factory() as session:
                chunk = session.get(Chunk, chunk_id)
                if chunk:
                    chunk.provider = provider
                    session.commit()

    def update_model(self, chunk_id: str, model: str) -> None:
        """Cập nhật tên mô hình cụ thể (model) đã thực hiện trích xuất."""
        with self._lock:
            with self._session_factory() as session:
                chunk = session.get(Chunk, chunk_id)
                if chunk:
                    chunk.model = model
                    session.commit()

    def mark_completed(
        self,
        chunk_id: str,
        result: Dict[str, Any],
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """Đánh dấu chunk đã hoàn thành xử lý và lưu trữ kết quả trích xuất cấu trúc."""
        with self._lock:
            with self._session_factory() as session:
                chunk = session.get(Chunk, chunk_id)
                if chunk:
                    chunk.graph_extraction = result
                    chunk.status = "COMPLETED"
                    if provider:
                        chunk.provider = provider
                    if model:
                        chunk.model = model
                    session.commit()

    def mark_failed(self, chunk_id: str, max_retries: int) -> str:
        """Tăng số lần thử lại (retry_count) và chuyển sang FAILED nếu vượt ngưỡng, ngược lại đưa về PENDING.

        Args:
            chunk_id: Mã định danh chunk gặp lỗi.
            max_retries: Số lần thử lại tối đa cho phép.

        Returns:
            str: Trạng thái mới của chunk ('PENDING', 'FAILED' hoặc 'NOT_FOUND').
        """
        with self._lock:
            with self._session_factory() as session:
                chunk = session.get(Chunk, chunk_id)
                if chunk:
                    chunk.retry_count += 1
                    chunk.status = "FAILED" if chunk.retry_count >= max_retries else "PENDING"
                    session.commit()
                    return chunk.status
                return "NOT_FOUND"
