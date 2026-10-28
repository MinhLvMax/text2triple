"""Module cấu hình môi trường và tham số hệ thống."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Xác định PROJECT_DIR (thư mục gốc của dự án chứa file .env)
PROJECT_DIR = Path(__file__).resolve().parents[2]  # Lên 2 cấp: infrastructure -> src -> project root
ENV_PATH = PROJECT_DIR / '.env'
load_dotenv(dotenv_path=ENV_PATH)


class Config:
    """Quản trị tập trung các biến môi trường và cấu hình hệ thống."""
    PROJECT_DIR = PROJECT_DIR
    DATA_DIR = PROJECT_DIR / 'data'
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Cấu hình API OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('OPEN_API_KEY')

    # Cấu hình API Groq
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')

    # Cấu hình API Google AI Studio / Gemini
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

    # Cấu hình máy chủ Ollama
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY')

    # Cấu hình kết nối cơ sở dữ liệu đồ thị Neo4j
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

    @classmethod
    def validate(cls):
        """Kiểm tra tính hợp lệ của các biến môi trường thiết yếu trước khi khởi động."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("Thiếu biến môi trường OPENAI_API_KEY trong file .env")
        if not cls.NEO4J_URI or not cls.NEO4J_PASSWORD:
            raise ValueError("Thiếu cấu hình kết nối Neo4j trong file .env")


if __name__ == '__main__':
    print(PROJECT_DIR)
