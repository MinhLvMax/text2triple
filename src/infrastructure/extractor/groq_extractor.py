"""Adapter trích xuất tri thức sử dụng nền tảng tăng tốc phần cứng Groq Cloud."""
import json
from typing import List, Type, Optional
from groq import Groq

from src.application.port.base_extractor import BaseExtractor
from src.domain.extraction_schema.extraction_result import ExtractionResult, build_extraction_model
from src.domain.extraction_schema.relations import BaseRelation
from src.infrastructure.extractor.prompt import build_system_prompt, build_user_prompt, clean_json_text, to_result

DEFAULT_MODEL = "openai/gpt-oss-120b"


class GroqExtractor(BaseExtractor):
    """Triển khai trích xuất dữ liệu qua Groq API tận dụng tốc độ phản hồi cao."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        self._client = Groq(api_key=api_key)
        self._model = model or DEFAULT_MODEL

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
