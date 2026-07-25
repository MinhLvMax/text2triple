from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]  # Đường dẫn file chính của dự án

LOG_FILES = BASE_DIR / 'logfiles'
LOG_FILES.mkdir(parents=True, exist_ok=True)

ENV_PATH = BASE_DIR / ".env"
if not ENV_PATH.exists():
    ENV_PATH.write_text(
        "GROQ_API_KEY=\n",
        encoding="utf-8"
    )

load_dotenv(ENV_PATH)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if __name__ == '__main__':
    print(BASE_DIR)
    print(GROQ_API_KEY)