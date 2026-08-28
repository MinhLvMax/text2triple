from pathlib import Path

class Config:
    PROJECT_DIR = Path(__file__).resolve().parents[1]

    DATA_DIR = PROJECT_DIR / 'data'
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    ENV_PATH = PROJECT_DIR / '.env'
    # if not ENV_PATH.exists():
    #     ENV_PATH.write_text(
    #         data='''HISTORY_PDF_DIR=''',
    #         encoding='utf-8'
    #     )
