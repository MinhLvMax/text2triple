import json
from typing import List, Optional, Type
from google import genai
from google.genai import types

from src.application.port.base_extractor import BaseExtractor
from src.domain.extraction_schema.extraction_result import ExtractionResult, build_extraction_model
from src.domain.extraction_schema.relations import BaseRelation
from src.infrastructure.extractor.prompt import (
    build_system_prompt,
    build_user_prompt,
    clean_json_text,
    to_result,
)

DEFAULT_MODEL = "gemini-2.5-flash"


class GoogleAIExtractor(BaseExtractor):
    """Adapter trích xuất tri thức sử dụng Google AI Studio (Gemini) qua official SDK `google-genai`."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        self._client = genai.Client(api_key=api_key)
        self._model = model or DEFAULT_MODEL

    def extract(
        self,
        chunk_id: str,
        text: str,
        relation_classes: List[Type[BaseRelation]],
    ) -> ExtractionResult:
        model = build_extraction_model(relation_classes)
        schema_str = json.dumps(model.model_json_schema(), ensure_ascii=False)

        system_instruction = (
            f"{build_system_prompt(relation_classes)}\n"
            f"Chỉ trả về đối tượng JSON hợp lệ, tuân theo JSON schema sau:\n{schema_str}"
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
        )

        response = self._client.models.generate_content(
            model=self._model,
            contents=build_user_prompt(chunk_id, text),
            config=config,
        )

        raw_content = response.text or "{}"
        cleaned_content = clean_json_text(raw_content)

        return to_result(chunk_id, model.model_validate_json(cleaned_content))
