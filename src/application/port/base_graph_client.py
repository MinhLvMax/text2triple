"""Cổng giao tiếp (Port) thao tác với cơ sở dữ liệu đồ thị."""
from abc import ABC, abstractmethod

from src.domain.extraction_schema.extraction_result import ExtractionResult


class BaseGraphClient(ABC):
    """Giao diện trừu tượng cho các Adapter tương tác và lưu trữ dữ liệu vào Graph Database."""

    @abstractmethod
    def ingest_extraction_result(self, result: ExtractionResult) -> None:
        """Nạp các quan hệ và thực thể tương ứng của một đoạn văn bản vào cơ sở dữ liệu đồ thị.

        Args:
            result: Kết quả trích xuất bao gồm chunk_id và các quan hệ ngữ nghĩa.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Giải phóng tài nguyên kết nối cơ sở dữ liệu."""
        raise NotImplementedError
