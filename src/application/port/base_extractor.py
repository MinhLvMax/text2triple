from abc import ABC, abstractmethod
from typing import List, Type

# Import đúng đường dẫn bạn vừa tạo
from src.domain.extraction_schema.extraction_result import ExtractionResult
# Import BaseRelation từ thư viện schema của bạn
from src.domain.extraction_schema.relations import BaseRelation


class BaseExtractor(ABC):
    """Cổng trích xuất thực thể/quan hệ từ văn bản."""

    @abstractmethod
    def extract(
        self,
        chunk_id: str,
        text: str,
        relation_classes: List[Type[BaseRelation]]  # Bổ sung tham số này
    ) -> ExtractionResult:
        """
        Trích xuất và trả về ExtractionResult đã validate.
        Chỉ trích xuất các quan hệ nằm trong `relation_classes`.
        Ném exception nếu thất bại.
        """
        raise NotImplementedError