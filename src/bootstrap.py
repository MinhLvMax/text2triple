"""Module Bootstrap - Bộ khởi tạo phụ thuộc (Dependency Injection / IoC Container).

Chịu trách nhiệm khởi tạo và kết nối các thành phần của hệ thống theo kiến trúc
Clean Architecture (Hexagonal Architecture), từ các Adapter hạ tầng (LLM, Graph DB,
SQLite Repository) tới tầng Application Use Cases.
"""
from typing import Literal, Optional

from src.application.port.base_extractor import BaseExtractor
from src.application.port.base_graph_client import BaseGraphClient
from src.application.usecases.extract import InformationExtractionUseCase
from src.infrastructure.config import Config

Provider = Literal["openai", "groq", "ollama", "google", "gemini"]


def build_extractor(provider: Provider = "openai", model: Optional[str] = None) -> BaseExtractor:
    """Khởi tạo thể hiện của BaseExtractor tương ứng với provider được chỉ định.

    Args:
        provider: Tên nhà cung cấp dịch vụ LLM ('openai', 'groq', 'ollama', 'google', 'gemini').
        model: Tên mô hình cụ thể (nếu là None, extractor sẽ dùng model mặc định của mình).

    Returns:
        BaseExtractor: Adapter trích xuất dữ liệu cụ thể.

    Raises:
        ValueError: Nếu thiếu API key hoặc tên provider không được hỗ trợ.
    """
    if provider == "openai":
        if not Config.OPENAI_API_KEY:
            raise ValueError("Thiếu OPENAI_API_KEY trong file .env")
        from src.infrastructure.extractor.openai_extractor import OpenAIExtractor
        return OpenAIExtractor(Config.OPENAI_API_KEY, model)
    if provider == "groq":
        if not Config.GROQ_API_KEY:
            raise ValueError("Thiếu GROQ_API_KEY trong file .env")
        from src.infrastructure.extractor.groq_extractor import GroqExtractor
        return GroqExtractor(Config.GROQ_API_KEY, model)
    if provider == "ollama":
        from src.infrastructure.extractor.ollama_extractor import OllamaExtractor
        return OllamaExtractor(
            api_key=Config.OLLAMA_API_KEY,
            model=model,
            host=Config.OLLAMA_HOST,
        )
    if provider in ("google", "gemini"):
        if not Config.GOOGLE_API_KEY:
            raise ValueError("Thiếu GOOGLE_API_KEY trong file .env")
        from src.infrastructure.extractor.google_extractor import GoogleAIExtractor
        return GoogleAIExtractor(api_key=Config.GOOGLE_API_KEY, model=model)
    raise ValueError(f"Provider không hỗ trợ: {provider}")


def build_graph_client() -> BaseGraphClient:
    """Khởi tạo client kết nối với cơ sở dữ liệu đồ thị Neo4j.

    Returns:
        BaseGraphClient: Adapter kết nối cơ sở dữ liệu đồ thị.
    """
    from src.infrastructure.graph_database.neo4j_graph_client import Neo4jGraphClient
    return Neo4jGraphClient(Config.NEO4J_URI, Config.NEO4J_USER, Config.NEO4J_PASSWORD)


def build_chunk_repository():
    """Khởi tạo Repository quản lý hàng đợi các đoạn văn bản (chunks) từ SQLite Staging.

    Returns:
        ChunkRepository: Đối tượng repository thao tác với bảng chunk.
    """
    from src.infrastructure.database.repositories import ChunkRepository
    return ChunkRepository()


def build_usecase(
    provider: Provider = "openai",
    model: Optional[str] = None,
) -> InformationExtractionUseCase:
    """Khởi tạo toàn bộ Use Case trích xuất tri thức với các phụ thuộc tương ứng.

    Args:
        provider: Tên nhà cung cấp LLM mong muốn.
        model: Tên mô hình mong muốn sử dụng.

    Returns:
        InformationExtractionUseCase: Thể hiện Use Case đã sẵn sàng thực thi.
    """
    return InformationExtractionUseCase(
        extractor=build_extractor(provider, model),
        graph_client=build_graph_client(),
    )
