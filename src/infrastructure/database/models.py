"""Mô hình ORM (SQLAlchemy) đại diện cho bảng lưu trữ tạm (Staging) trong SQLite."""
import re
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import String, Text, JSON, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr, MappedAsDataclass


class Base(MappedAsDataclass, DeclarativeBase):
    """Lớp cơ sở ánh xạ bảng ORM tự động quy đổi tên lớp CamelCase sang snake_case."""
    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name


class Chunk(Base):
    """Thực thể ánh xạ bảng chunk lưu trữ dữ liệu các đoạn văn bản trong hàng đợi xử lý."""

    # Khóa chính định danh duy nhất đoạn văn bản
    chunk_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        comment="Mã định danh duy nhất của chunk"
    )

    # Nội dung văn bản cốt lõi
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Nội dung văn bản để gửi cho LLM hoặc Embedding"
    )

    # Dữ liệu thuộc tính mở rộng (tên sách, số trang, tác giả, v.v.)
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Chứa toàn bộ thông tin phụ: book_name, page, author, words, sentences..."
    )

    # Trạng thái tiến trình trong hàng đợi: PENDING, PROCESSING, COMPLETED, FAILED
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        index=True,
        comment="PENDING, PROCESSING, COMPLETED, FAILED"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        init=False
    )

    # Số lần thử lại khi gặp sự cố
    retry_count: Mapped[int] = mapped_column(default=0)

    # Kết quả trích xuất cấu trúc đồ thị (dạng JSON)
    graph_extraction: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Kết quả trích xuất thực thể và quan hệ"
    )

    # Nội dung văn bản mở rộng bao gồm ngữ cảnh gối đầu (overlap)
    chunk_overlap_200: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Text của chunk kèm 200 ký tự cuối trang trước và 200 ký tự đầu trang sau"
    )

    # Nhà cung cấp mô hình thực hiện trích xuất (openai, groq, google, ollama)
    provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        comment="Nhà cung cấp LLM: openai, groq, ollama, google"
    )

    # Tên định danh mô hình cụ thể
    model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        comment="Tên model thực hiện trích xuất"
    )
