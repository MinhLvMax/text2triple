"""Cổng giao tiếp (Port) trích xuất tri thức từ văn bản."""
from abc import ABC, abstractmethod
from typing import List, Type

from src.domain.extraction_schema.extraction_result import ExtractionResult
from src.domain.extraction_schema.relations import BaseRelation


class BaseExtractor(ABC):
    """Giao diện trừu tượng cho các Adapter trích xuất thực thể và quan hệ thông qua LLM."""

    @abstractmethod
    def extract(
        self,
        chunk_id: str,
        text: str,
        relation_classes: List[Type[BaseRelation]]
    ) -> ExtractionResult:
        """Thực hiện trích xuất các quan hệ ngữ nghĩa từ đoạn văn bản đầu vào.

        Args:
            chunk_id: Mã định danh duy nhất của đoạn văn bản (chunk).
            text: Nội dung văn bản cần phân tích và trích xuất.
            relation_classes: Danh sách các lớp quan hệ mục tiêu được phép trích xuất.

        Returns:
            ExtractionResult: Đối tượng chứa chunk_id và danh sách quan hệ đã kiểm thực.

        Raises:
            Exception: Khi phát sinh lỗi trong quá trình giao tiếp với mô hình hoặc phân giải dữ liệu.
        """
        raise NotImplementedError
