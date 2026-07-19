from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]  # Đường dẫn file chính của dự án


if __name__ == '__main__':
    print(BASE_DIR)