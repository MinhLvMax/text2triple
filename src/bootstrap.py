from typing import Literal, Optional

from src.application.port.base_extractor import BaseExtractor
from src.application.port.base_graph_client import BaseGraphClient
from src.application.usecases.extract import InformationExtractionUseCase
from src.infrastructure.config import Config

Provider = Literal["openai", "groq", "ollama", "google", "gemini"]


def build_extractor(provider: Provider = "openai", model: Optional[str] = None) -> BaseExtractor:
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
    from src.infrastructure.graph_database.neo4j_graph_client import Neo4jGraphClient
    return Neo4jGraphClient(Config.NEO4J_URI, Config.NEO4J_USER, Config.NEO4J_PASSWORD)


def build_chunk_repository():
    from src.infrastructure.database.repositories import ChunkRepository
    return ChunkRepository()


def build_usecase(
    provider: Provider = "openai",
    model: Optional[str] = None,
) -> InformationExtractionUseCase:
    return InformationExtractionUseCase(
        extractor=build_extractor(provider, model),
        graph_client=build_graph_client(),
    )
