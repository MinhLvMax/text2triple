"""Adapter trích xuất tri thức sử dụng Ollama qua chuẩn OpenAI-compatible endpoint."""
import json
from typing import List, Optional, Type
from openai import OpenAI

from src.application.port.base_extractor import BaseExtractor
from src.domain.extraction_schema.extraction_result import ExtractionResult, build_extraction_model
from src.domain.extraction_schema.relations import BaseRelation
from src.infrastructure.extractor.prompt import (
    build_system_prompt,
    build_user_prompt,
    clean_json_text,
    to_result,
)

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b"


class OllamaExtractor(BaseExtractor):
    """Adapter trích xuất tri thức sử dụng Ollama qua OpenAI-compatible API endpoint (/v1).

    Hỗ trợ kết nối cả môi trường Ollama chạy trên máy cục bộ (Local) hoặc máy chủ từ xa.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        host: Optional[str] = None,
        timeout: float = 180.0,
    ):
        base_url = (host or DEFAULT_HOST).rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"

        self._model = model or DEFAULT_MODEL
        # Ollama cục bộ không bắt buộc API key nhưng OpenAI client yêu cầu chuỗi không rỗng
        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key or "ollama",
            timeout=timeout,
        )

    def extract(
        self,
        chunk_id: str,
        text: str,
        relation_classes: List[Type[BaseRelation]],
    ) -> ExtractionResult:
        model = build_extraction_model(relation_classes)
        schema = json.dumps(model.model_json_schema(), ensure_ascii=False)
        system = (
            f"{build_system_prompt(relation_classes)}\n"
            f"Chỉ trả về một đối tượng JSON hợp lệ, không kèm giải thích, tuân theo JSON schema:\n{schema}"
        )

        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": build_user_prompt(chunk_id, text)},
            ],
            response_format={"type": "json_object"},
        )
        raw_content = completion.choices[0].message.content or "{}"
        cleaned_content = clean_json_text(raw_content)
        return to_result(chunk_id, model.model_validate_json(cleaned_content))
