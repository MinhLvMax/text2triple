"""Mô hình đóng gói kết quả trích xuất và kiến tạo mô hình Pydantic động.

Cung cấp lớp dữ liệu ExtractionResult và hàm tiện ích xây dựng mô hình
kiểm thực động (dynamic schema) phục vụ Structured Output từ các mô hình LLM.
"""
from typing import Annotated, Any, List, Type, Union
from pydantic import BaseModel, Field, create_model

from src.domain.extraction_schema.relations import BaseRelation


class ExtractionResult(BaseModel):
    """Đối tượng kết quả chứa các quan hệ ngữ nghĩa đã trích xuất của một đoạn văn bản."""
    chunk_id: str
    relations: List[Any] = Field(
        default_factory=list,
        description="Danh sách các đối tượng quan hệ ngữ nghĩa kế thừa từ BaseRelation"
    )


def build_extraction_model(relation_classes: List[Type[BaseRelation]]) -> Type[BaseModel]:
    """Xây dựng mô hình Pydantic động chứa danh sách quan hệ được cấu hình hợp lệ.

    Mô hình trả về được sử dụng làm JSON Schema truyền vào LLM (Structured Outputs).
    Trường `chunk_id` được lược bỏ ở bước này để tránh việc mô hình ngôn ngữ sao chép sai lệch,
    và sẽ được gắn bổ sung ở tầng Use Case.

    Args:
        relation_classes: Danh sách các lớp quan hệ cho phép trích xuất.

    Returns:
        Type[BaseModel]: Lớp Pydantic động định nghĩa cấu trúc kết quả mong đợi từ LLM.

    Raises:
        ValueError: Nếu danh sách quan hệ rỗng.
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
