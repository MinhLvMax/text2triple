from typing import List, Type

from openai import OpenAI

from src.application.port.base_extractor import BaseExtractor
from src.domain.extraction_schema.extraction_result import ExtractionResult, build_extraction_model
from src.domain.extraction_schema.relations import BaseRelation
from src.infrastructure.extractor.prompt import build_system_prompt, build_user_prompt, clean_json_text, to_result

DEFAULT_MODEL = "gpt-5.6-luna"


class OpenAIExtractor(BaseExtractor):
    def __init__(self, api_key: str, model: str | None = None):
        self._client = OpenAI(api_key=api_key)
        self._model = model or DEFAULT_MODEL

    def extract(
        self,
        chunk_id: str,
        text: str,
        relation_classes: List[Type[BaseRelation]],
    ) -> ExtractionResult:
        model = build_extraction_model(relation_classes)
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": build_system_prompt(relation_classes)},
                {"role": "user", "content": build_user_prompt(chunk_id, text)},
            ],
            # strict=False vì `metadata` là dict[str, str] (khóa do LLM tự đặt),
            # chế độ strict của OpenAI không chấp nhận dict tự do.
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "extraction",
                    "schema": model.model_json_schema(),
                    "strict": False,
                },
            },
        )
        message = completion.choices[0].message
        if message.refusal:
            raise RuntimeError(f"OpenAI từ chối: {message.refusal}")
        raw_content = message.content or "{}"
        cleaned_content = clean_json_text(raw_content)
        return to_result(chunk_id, model.model_validate_json(cleaned_content))
