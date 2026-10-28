"""Tầng nghiệp vụ (Application Use Cases) - Điều phối quy trình trích xuất và lưu trữ đồ thị."""
import hashlib
import logging
from typing import Optional, Dict, Any, List, Type

from src.application.port.base_extractor import BaseExtractor
from src.application.port.base_graph_client import BaseGraphClient
from src.domain.extraction_schema.extraction_result import ExtractionResult
from src.domain.extraction_schema.relations import BaseRelation

logger = logging.getLogger(__name__)


class InformationExtractionUseCase:
    """Nghiệp vụ điều phối trích xuất tri thức từ văn bản và lưu trữ vào cơ sở dữ liệu đồ thị."""

    def __init__(self, extractor: BaseExtractor, graph_client: BaseGraphClient):
        """Khởi tạo Use Case với các phụ thuộc được tiêm từ bên ngoài (Dependency Injection).

        Args:
            extractor: Adapter thực hiện trích xuất dữ liệu qua LLM.
            graph_client: Adapter lưu trữ và thao tác với cơ sở dữ liệu đồ thị.
        """
        self._extractor = extractor
        self._graph_client = graph_client

    def _generate_chunk_id(self, text: str) -> str:
        """Tự động sinh mã định danh duy nhất (chunk_id) dựa trên hàm băm MD5 của nội dung."""
        text_hash = hashlib.md5(text.strip().encode("utf-8")).hexdigest()[:10]
        return f"chunk_{text_hash}"

    def execute(
        self,
        text: str,
        relation_classes: List[Type[BaseRelation]],
        chunk_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """Thực thi luồng trích xuất tri thức: Gọi Extractor -> Ghi nhận vào Graph Database.

        Args:
            text: Đoạn văn bản đầu vào cần trích xuất tri thức.
            relation_classes: Danh sách các lớp quan hệ mục tiêu cần trích xuất.
            chunk_id: Mã định danh chunk (nếu None sẽ tự sinh theo hàm băm).
            metadata: Metadata ngữ cảnh bổ sung cho đoạn văn bản (tùy chọn).

        Returns:
            ExtractionResult: Kết quả trích xuất bao gồm danh sách các quan hệ và thực thể.

        Raises:
            ValueError: Nếu nội dung văn bản rỗng hoặc không cung cấp lớp quan hệ nào.
            Exception: Khi phát sinh lỗi trong quá trình trích xuất hoặc nạp dữ liệu.
        """
        clean_text = text.strip() if text else ""
        if not clean_text:
            raise ValueError("Nội dung văn bản đầu vào không được để trống.")

        if not relation_classes:
            raise ValueError("Phải cung cấp ít nhất 1 class quan hệ để trích xuất.")

        assigned_chunk_id = chunk_id or self._generate_chunk_id(clean_text)
        logger.info("Bắt đầu xử lý trích xuất cho chunk: %s", assigned_chunk_id)

        try:
            # 1. Thực hiện trích xuất cấu trúc quan hệ ngữ nghĩa qua Extractor
            extraction_result: ExtractionResult = self._extractor.extract(
                chunk_id=assigned_chunk_id,
                text=clean_text,
                relation_classes=relation_classes
            )

            # 2. Nạp dữ liệu vào cơ sở dữ liệu đồ thị nếu có quan hệ được phát hiện
            if extraction_result.relations:
                self._graph_client.ingest_extraction_result(extraction_result)
                logger.info("Đã nạp thành công chunk %s vào CSDL đồ thị.", assigned_chunk_id)
            else:
                logger.warning("Không tìm thấy quan hệ nào trong chunk %s.", assigned_chunk_id)

            return extraction_result

        except Exception as e:
            logger.error("Lỗi trích xuất cho chunk %s: %s", assigned_chunk_id, str(e), exc_info=True)
            raise e

    def close(self) -> None:
        """Giải phóng tài nguyên kết nối đồ thị."""
        self._graph_client.close()
