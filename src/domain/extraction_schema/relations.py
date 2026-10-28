"""Mô hình dữ liệu quan hệ (Relation Schemas) trong miền tri thức Lịch sử Việt Nam.

Định nghĩa các lớp quan hệ ngữ nghĩa (Semantic Relationships) kế thừa từ BaseRelation,
ràng buộc chặt chẽ miền chủ thể (domain) và miền đích (range) giữa các thực thể,
đồng thời lưu giữ bằng chứng xác thực (evidence) trích xuất từ văn bản nguồn.
"""
from typing import Any, Union, Literal
from pydantic import BaseModel, Field

from src.domain.extraction_schema.entities import (
    Person,
    Event,
    WeaponTactic,
    Location,
    Organization,
    Concept,
    DocumentPolicy,
    DynastyEra,
    TimePeriod,
)


class BaseRelation(BaseModel):
    """Quan hệ cơ sở lưu trữ liên kết giữa các thực thể và bằng chứng ngữ cảnh."""
    evidence: str = Field(
        description="Trích xuất CHÍNH XÁC nguyên văn một câu hoặc đoạn ngắn từ văn bản chứa thông tin chứng minh cho mối quan hệ này. Tuyệt đối không tự sáng tác hoặc diễn đạt lại."
    )
    # Thuộc tính bổ trợ lưu trữ ngữ cảnh hành động
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Các thông tin NGỮ CẢNH bổ sung cho mối quan hệ/hành động này (nếu có). "
            "ƯU TIÊN tìm kiếm và trích xuất các khía cạnh sau (tự đặt tên key tiếng Anh hoặc tiếng Việt không dấu): "
            "1. Thời gian (time / period) "
            "2. Mục đích / Nguyên nhân (purpose / reason) "
            "3. Vai trò cụ thể (role / position) "
            "4. Kết quả / Mức độ (outcome / degree) "
            "5. Phương thức thực hiện (method). "
        )
    )


# ==============================================================================
# NHÓM QUAN HỆ QUÂN SỰ, CHIẾN TRANH VÀ SỰ KIỆN
# ==============================================================================

class LanhDaoRelation(BaseRelation):
    """Nhân vật hoặc Tổ chức lãnh đạo một trận đánh hoặc cuộc khởi nghĩa"""
    relation_name: Literal["LANH_DAO"] = "LANH_DAO"
    # Miền chủ thể: Cá nhân hoặc tổ chức nắm quyền chỉ huy
    domain: Union[Person, Organization] = Field(
        description="Chủ thể nắm quyền lãnh đạo, chỉ huy (VD: Vua, Tướng lĩnh, Đảng, Triều đình)."
    )
    # Miền đích: Sự kiện được lãnh đạo
    range: Event = Field(
        description="Sự kiện, cuộc khởi nghĩa, trận chiến hoặc phong trào chịu sự lãnh đạo."
    )


class SuDungRelation(BaseRelation):
    """Sử dụng vũ khí, phương tiện hoặc địa hình/địa danh làm chiến thuật"""
    relation_name: Literal["SU_DUNG"] = "SU_DUNG"
    domain: Union[Person, Organization] = Field(
        description="Chủ thể thực hiện hành động sử dụng (Người hoặc Tổ chức)."
    )
    range: Union[WeaponTactic, Location] = Field(
        description="Vũ khí, khí tài, phương tiện, chiến thuật, hoặc địa hình/địa danh được đem ra lợi dụng (VD: cọc bọc sắt, sông Bạch Đằng, hỏa công)."
    )


class DienRaTaiRelation(BaseRelation):
    """Sự kiện diễn ra tại một địa danh cụ thể"""
    relation_name: Literal["DIEN_RA_TAI"] = "DIEN_RA_TAI"
    domain: Event = Field(
        description="Sự kiện, trận đánh, hội nghị hoặc phong trào lịch sử."
    )
    range: Location = Field(
        description="Địa danh cụ thể, tên dòng sông, ngọn núi, làng xã, thành trì nơi sự kiện đó tọa lạc."
    )


class ThamGiaRelation(BaseRelation):
    """Tổ chức, cá nhân hoặc triều đại tham gia vào sự kiện"""
    relation_name: Literal["THAM_GIA"] = "THAM_GIA"
    domain: Union[Person, Organization, DynastyEra] = Field(
        description="Lực lượng quân sự, quần chúng nhân dân, tổ chức hoặc cá nhân góp mặt."
    )
    range: Event = Field(
        description="Sự kiện, trận chiến hoặc phong trào mà chủ thể đã tham gia."
    )


# ==============================================================================
# NHÓM QUAN HỆ CHÍNH TRỊ, TRIỀU ĐẠI & HÀNH CHÍNH
# ==============================================================================

class ThanhLapRelation(BaseRelation):
    """Thành lập, xây dựng triều đại, tổ chức, hoặc địa danh/công trình"""
    relation_name: Literal["THANH_LAP"] = "THANH_LAP"
    domain: Union[Person, Organization, DynastyEra] = Field(
        description="Cá nhân, tổ chức hoặc triều đại đứng ra khởi xướng, xây dựng, thành lập."
    )
    range: Union[Organization, Location, DynastyEra, Event, DocumentPolicy] = Field(
        description="Tổ chức mới, quốc gia/triều đại mới, sự kiện mới, văn kiện mới, hoặc công trình/kinh đô/địa giới hành chính mới được tạo ra (VD: Nhà nước Âu Lạc, thành Cổ Loa)."
    )


class BanHanhRelation(BaseRelation):
    """Ban hành chính sách, đạo luật, hiệp ước hoặc sáng tác tác phẩm"""
    relation_name: Literal["BAN_HANH"] = "BAN_HANH"
    domain: Union[Person, Organization, DynastyEra] = Field(
        description="Cá nhân (vua, tác giả), tổ chức (quốc hội, triều đình) hoặc triều đại thực hiện việc ban hành."
    )
    range: DocumentPolicy = Field(
        description="Văn kiện, đạo luật, hiệp ước, sách lệnh, hoặc tác phẩm cụ thể được công bố (VD: Chiếu dời đô, Hiệp định Paris)."
    )


class KeViRelation(BaseRelation):
    """Kế nghiệp ngai vàng, chức vụ, hoặc triều đại này thay thế triều đại khác"""
    relation_name: Literal["KE_VI"] = "KE_VI"
    domain: Union[Person, DynastyEra] = Field(
        description="Người lên ngôi vua, người kế nhiệm chức vụ, hoặc triều đại mới lên nắm quyền."
    )
    range: Union[Person, DynastyEra] = Field(
        description="Người tiền nhiệm (vua đời trước), hoặc triều đại cũ bị lật đổ/thay thế."
    )


class ThuocVeRelation(BaseRelation):
    """Phân cấp địa lý hành chính hoặc tổ chức trực thuộc"""
    relation_name: Literal["THUOC_VE"] = "THUOC_VE"
    domain: Union[Location, Organization, Person] = Field(
        description="Thực thể con, cấp dưới (VD: cấp huyện, xã, đơn vị quân đội nhỏ, tướng lĩnh dưới quyền)."
    )
    range: Union[Location, Organization, DynastyEra] = Field(
        description="Thực thể cha, cấp trên, đơn vị quản lý lớn hơn (VD: tỉnh, quốc gia, triều đại, bộ chỉ huy)."
    )


# ==============================================================================
# NHÓM QUAN HỆ NHÂN QUẢ & THỜI GIAN
# ==============================================================================

class DanDenRelation(BaseRelation):
    """Nguyên nhân và Kết quả (rất quan trọng cho phân tích lịch sử)"""
    relation_name: Literal["DAN_DEN"] = "DAN_DEN"
    domain: Union[Event, DocumentPolicy, Concept] = Field(
        description="Sự kiện, trận đánh, chính sách/văn kiện, hoặc một khái niệm/tư tưởng đóng vai trò là NGUYÊN NHÂN khởi phát."
    )
    range: Union[Event, Concept, DocumentPolicy] = Field(
        description="Sự kiện tiếp theo, kết quả, một khái niệm/trào lưu mới, hoặc một chính sách/văn kiện mới là HỆ QUẢ trực tiếp."
    )


class DienRaVaoRelation(BaseRelation):
    """Gắn kết Sự kiện, Triều đại với mốc Thời gian cụ thể"""
    relation_name: Literal["DIEN_RA_VAO"] = "DIEN_RA_VAO"
    domain: Union[Event, DynastyEra, DocumentPolicy] = Field(
        description="Sự kiện, kỷ nguyên triều đại, hoặc văn kiện được công bố."
    )
    range: Union[TimePeriod, DynastyEra] = Field(
        description="Mốc thời gian, năm, thế kỷ, triều đại, hoặc niên hiệu cụ thể (VD: năm 938, thế kỷ XV)."
    )
