from typing import List, Literal
from pydantic import BaseModel, Field

class Entity(BaseModel):
    name: str = Field(description="Tên thực thể chuẩn hóa, viết hoa chữ cái đầu (VD: Ngô Quyền, Sông Bạch Đằng)")
    type: Literal["PERSON", "EVENT", "LOCATION", "ORGANIZATION", "WEAPON_TACTIC"] = Field(
        description="Loại thực thể thuộc danh mục cho trước"
    )
    description: str = Field(description="Mô tả vai trò hoặc đặc điểm của thực thể trong ngữ cảnh đoạn văn")

class Relationship(BaseModel):
    source: str = Field(description="Tên thực thể nguồn, phải trùng khớp với `name` trong danh sách entities")
    target: str = Field(description="Tên thực thể đích, phải trùng khớp với `name` trong danh sách entities")
    relation: Literal[
        "CHỈ_HUY", "LÃNH_ĐẠO", "SỬ_DỤNG", "BỐ_TRÍ_TẠI",
        "DIỄN_RA_TẠI", "ĐÁNH_BẠI", "TỬ_TRẬN_TẠI"
    ] = Field(description="Mối quan hệ chuẩn hóa viết in hoa")
    evidence: str = Field(description="Câu văn gốc trong tài liệu chứng minh cho mối quan hệ này")

class ExtractionResult(BaseModel):
    chunk_id: str = Field(description="Mã định danh của đoạn văn bản")
    entities: List[Entity]
    relationships: List[Relationship]