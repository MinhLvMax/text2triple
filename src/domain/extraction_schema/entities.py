from typing import Any, Literal
from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    name: str = Field(description="Tên thực thể chuẩn hóa")
    description: str = Field(description="Mô tả vai trò ngắn gọn trong ngữ cảnh")
    # Định nghĩa sẵn trường type ở Base để hệ thống nhận diện đây là thuộc tính chung
    type: str = Field(description="Loại thực thể")
    # Cho LLM tự trích xuất thêm thuộc tính của Node
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Các thông tin thuộc tính CỐ ĐỊNH gắn liền với thực thể này (nếu có). "
            "Gợi ý ưu tiên tìm kiếm: năm sinh/năm mất, quê quán, nghề nghiệp, "
            "tên gọi khác (alias), chức vụ, hoặc quy mô/kích thước."
        )
    )


# Định nghĩa các loại thực thể cụ thể và "khóa" chặt trường type
class Person(BaseEntity):
    """Nhân vật lịch sử cụ thể (vua, tướng, học giả)"""
    type: Literal["Person"] = "Person"


class Event(BaseEntity):
    """Sự kiện, trận đánh, phong trào lịch sử"""
    type: Literal["Event"] = "Event"


class Location(BaseEntity):
    """Địa danh, sông, núi, thành lũy"""
    type: Literal["Location"] = "Location"


class WeaponTactic(BaseEntity):
    """Vũ khí, khí tài, phương tiện, chiến thuật"""
    type: Literal["WeaponTactic"] = "WeaponTactic"


class Organization(BaseEntity):
    """Tổ chức, triều đình, lực lượng quân sự"""
    type: Literal["Organization"] = "Organization"


class DynastyEra(BaseEntity):
    """Triều đại, Nhà nước hoặc Thời kỳ lịch sử (VD: Nhà Đinh, Đại Việt, Thời Bắc thuộc)"""
    type: Literal["DynastyEra"] = "DynastyEra"


class TimePeriod(BaseEntity):
    """Mốc thời gian, niên hiệu, kỷ nguyên (VD: Thế kỷ XV, Năm 938, Niên hiệu Thái Bình)"""
    type: Literal["TimePeriod"] = "TimePeriod"


class DocumentPolicy(BaseEntity):
    """Văn kiện, đạo luật, hiệp ước, chính sách, tác phẩm (VD: Chiếu Dời Đô, Luật Hồng Đức, Hiệp định Paris)"""
    type: Literal["DocumentPolicy"] = "DocumentPolicy"


class Concept(BaseEntity):
    """Khái niệm, tư tưởng, tôn giáo, chỉ số kinh tế-xã hội (VD: Nho giáo, Kinh tế thị trường, Diện tích phủ sóng)"""
    type: Literal["Concept"] = "Concept"
