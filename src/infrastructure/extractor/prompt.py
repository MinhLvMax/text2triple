from typing import List, Type

from pydantic import BaseModel

from src.domain.extraction_schema.extraction_result import ExtractionResult
from src.domain.extraction_schema.relations import BaseRelation


def build_system_prompt(relation_classes: List[Type[BaseRelation]]) -> str:
    relation_lines = "\n".join(
        f"- {cls.model_fields['relation_name'].default}: {(cls.__doc__ or '').strip()}"
        for cls in relation_classes
    )
    return (
        "Bạn là chuyên gia trích xuất tri thức lịch sử Việt Nam.\n"
        "Từ đoạn văn bản được cung cấp, hãy trích xuất các quan hệ giữa các thực thể.\n\n"
        "Các loại quan hệ được phép (relation_name: ý nghĩa):\n"
        f"{relation_lines}\n\n"
        "Quy tắc:\n"
        "- Chỉ dùng thông tin có trong văn bản, không suy diễn thêm.\n"
        "- Mỗi quan hệ có `domain` và `range` là thực thể đúng loại (`type`) mà schema cho phép.\n"
        "- `name` của thực thể phải chuẩn hóa, nhất quán giữa các quan hệ.\n"
        "- `evidence` là câu gốc trong văn bản chứng minh quan hệ.\n"
        "- Văn bản có thể có phần ngữ cảnh đầu/cuối (đánh dấu bằng '...') thuộc trang khác; ưu tiên nội dung chính.\n"
        "- Nếu không có gì để trích xuất, trả về danh sách `relations` rỗng.\n"
    )


def build_user_prompt(chunk_id: str, text: str) -> str:
    return f"chunk_id: {chunk_id}\n\nVăn bản:\n{text}"


def clean_json_text(text: str) -> str:
    """Loại bỏ markdown code fences (```json ... ```) nếu LLM vô tình kèm theo."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def to_result(chunk_id: str, parsed: BaseModel) -> ExtractionResult:
    """Gói kết quả LLM vào ExtractionResult của domain, gán chunk_id."""
    return ExtractionResult(chunk_id=chunk_id, relations=list(parsed.relations))
