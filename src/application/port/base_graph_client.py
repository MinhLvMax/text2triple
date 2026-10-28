from abc import ABC, abstractmethod

from src.domain.extraction_schema.extraction_result import ExtractionResult


class BaseGraphClient(ABC):
    """Cổng (port) thao tác với CSDL đồ thị."""

    @abstractmethod
    def ingest_extraction_result(self, result: ExtractionResult) -> None:
        """Ghi các quan hệ (và thực thể domain/range) của một chunk vào đồ thị."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Giải phóng kết nối."""
        raise NotImplementedError
