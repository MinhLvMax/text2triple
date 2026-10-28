from typing import Annotated, Any, List, Type, Union
from pydantic import BaseModel, Field, create_model

from src.domain.extraction_schema.relations import BaseRelation


class ExtractionResult(BaseModel):
    """Kết quả trả về từ tầng Infrastructure (Extractor) đưa lên Use Case"""
    chunk_id: str
    relations: List[Any] = Field(
        default_factory=list,
        description="Chứa trực tiếp các object quan hệ (VD: LanhDaoRelation, ThamGiaRelation...)"
    )


def build_extraction_model(relation_classes: List[Type[BaseRelation]]) -> Type[BaseModel]:
    """Dựng model mà LLM phải điền: `relations` chỉ chứa các loại quan hệ được phép.

    Không có `chunk_id` vì extractor tự gán, tránh việc LLM chép sai ID.
    """
    if not relation_classes:
        raise ValueError("Phải cung cấp ít nhất 1 class quan hệ.")
    if len(relation_classes) == 1:
        relation_type = relation_classes[0]
    else:
        relation_type = Annotated[
            Union[tuple(relation_classes)],
            Field(discriminator="relation_name"),
        ]
    return create_model(
        "LLMExtraction",
        relations=(List[relation_type], Field(default_factory=list)),
    )
