import threading
from pathlib import Path
import json
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.infrastructure.config import Config
from src.infrastructure.database.models import Chunk

# 1. Đường dẫn file database (Lưu vào thư mục data/)
DB_PATH = Config.DATA_DIR / "historical_knowledge" / "staging_chunks.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 2. Khởi tạo Engine
# echo=False để tắt log SQL (xử lý hàng nghìn chunk); đổi thành True để xem câu lệnh SQL trên console
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"timeout": 60},
    json_serializer=lambda obj: json.dumps(
        obj,
        ensure_ascii=False
    )
)

# 3. Tạo Session factory để thao tác dữ liệu sau này
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ChunkRepository:
    # KHÓA CẤP CLASS (Class-level lock):
    # Dùng chung cho TOÀN BỘ các instance của ChunkRepository trong tiến trình.
    # Ngăn tuyệt đối tình trạng 2 worker độc lập khởi tạo 2 instance repo khác nhau
    # rồi bốc trùng 1 chunk.
    _lock = threading.Lock()

    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self._session_factory = session_factory

    def fetch_pending(self, limit: Optional[int] = None) -> List[Tuple[str, str]]:
        """Trả về [(chunk_id, text gửi cho LLM)] của các chunk PENDING."""
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
        """Lấy nguyên tử (atomic) đúng 1 chunk PENDING và chuyển ngay sang PROCESSING.

        Sử dụng kết hợp 2 lớp bảo vệ chống Race Condition:
        1. Class-level threading.Lock: Đồng bộ hóa toàn bộ các thread trong cùng tiến trình.
        2. SQLite UPDATE ... RETURNING nguyên tử: Đảm bảo độc quyền ngay cả khi chạy
           trên nhiều tiến trình / terminal khác nhau.
        Trả về (chunk_id, text) hoặc None nếu không còn chunk nào PENDING.
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
        """Khôi phục các chunk đang bị kẹt ở trạng thái PROCESSING về lại PENDING.

        Rất hữu ích khi một tiến trình worker bị dừng đột ngột (mất điện, tắt console, Ctrl+C).
        Trả về số lượng chunk đã được khôi phục.
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
        """Cập nhật tên nhà cung cấp (provider) thực hiện trích xuất cho chunk."""
        with self._lock:
            with self._session_factory() as session:
                chunk = session.get(Chunk, chunk_id)
                if chunk:
                    chunk.provider = provider
                    session.commit()

    def update_model(self, chunk_id: str, model: str) -> None:
        """Cập nhật tên model thực hiện trích xuất cho chunk."""
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
        """Đánh dấu chunk đã xử lý thành công, lưu kết quả trích xuất và tùy chọn cập nhật provider/model."""
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
        """Tăng retry_count; FAILED nếu vượt ngưỡng, ngược lại giữ PENDING. Trả về status mới."""
        with self._lock:
            with self._session_factory() as session:
                chunk = session.get(Chunk, chunk_id)
                if chunk:
                    chunk.retry_count += 1
                    chunk.status = "FAILED" if chunk.retry_count >= max_retries else "PENDING"
                    session.commit()
                    return chunk.status
                return "NOT_FOUND"
