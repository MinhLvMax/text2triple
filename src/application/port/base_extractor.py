from src.domain.extraction_result import ExtractionResult


class Extractor:
    def extract(self, text: str) -> ExtractionResult:
        ...
