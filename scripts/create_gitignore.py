from scripts.config import PROJECT_PATH

from pathlib import Path

GITIGNORE_CONTENT = """
__pycache__/
*.pyc
.idea/
.venv/
.env
"""


def create_gitignore():
    file = PROJECT_PATH / ".gitignore"

    if file.exists():
        print('Đã có file .gitignore rồi')
        return

    file.write_text(
        GITIGNORE_CONTENT.strip(),
        encoding="utf-8"
    )

if __name__ == '__main__':
    create_gitignore()