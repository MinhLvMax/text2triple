import hashlib
import logging
from typing import Optional, Dict, Any, List, Type

from src.application.port.base_extractor import BaseExtractor
from src.application.port.base_graph_client import BaseGraphClient
from src.domain.extraction_schema.extraction_result import ExtractionResult
from src.domain.extraction_schema.relations import BaseRelation  # Import BaseRelation

logger = logging.getLogger(__name__)


class InformationExtractionUseCase:
    """Nghiệp vụ điều phối trích xuất tri thức từ văn bản và lưu vào Neo4j."""

    def __init__(self, extractor: BaseExtractor, graph_client: BaseGraphClient):
        self._extractor = extractor
        self._graph_client = graph_client

    def _generate_chunk_id(self, text: str) -> str:
        text_hash = hashlib.md5(text.strip().encode("utf-8")).hexdigest()[:10]
        return f"chunk_{text_hash}"

    def execute(
            self,
            text: str,
            relation_classes: List[Type[BaseRelation]],  # <-- THÊM THAM SỐ NÀY
            chunk_id: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        clean_text = text.strip() if text else ""
        if not clean_text:
            raise ValueError("Nội dung văn bản đầu vào không được để trống.")

        if not relation_classes:
            raise ValueError("Phải cung cấp ít nhất 1 class quan hệ để trích xuất.")

        assigned_chunk_id = chunk_id or self._generate_chunk_id(clean_text)
        logger.info("Bắt đầu xử lý trích xuất cho chunk: %s", assigned_chunk_id)

        try:
            # Truyền relation_classes xuống Extractor
            extraction_result: ExtractionResult = self._extractor.extract(
                chunk_id=assigned_chunk_id,
                text=clean_text,
                relation_classes=relation_classes
            )

            # Hàm ingest_extraction_result của bạn đang mong đợi cấu trúc Flat (entities, relationships)
            # Chúng ta sẽ giữ nguyên việc gọi hàm này, nhưng Adapter sẽ phải format data cho khớp.
            if extraction_result.relations:
                # Chuyển đổi từ dynamic relations sang dạng FlatEntity/FlatRelationship cho Neo4j
                # (Sẽ thực hiện việc chuyển đổi này ngay bên trong Adapter OpenAI/Groq cho tiện)
                self._graph_client.ingest_extraction_result(extraction_result)
                logger.info(f"Đã nạp thành công chunk {assigned_chunk_id}.")
            else:
                logger.warning("Không tìm thấy quan hệ nào trong chunk %s.", assigned_chunk_id)

            return extraction_result

        except Exception as e:
            logger.error("Lỗi trích xuất cho chunk %s: %s", assigned_chunk_id, str(e), exc_info=True)
            raise e

    def close(self) -> None:
        """Giải phóng tài nguyên (kết nối đồ thị)."""
        self._graph_client.close()
