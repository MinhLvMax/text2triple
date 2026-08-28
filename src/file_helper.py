import json
from pathlib import Path
from typing import Any, Union

PathLike = Union[str, Path]

class FileHelper:
    """Tập hợp các tiện ích đọc/ghi file text và JSON."""

    @staticmethod
    def read_text(path: PathLike, encoding: str = "utf-8") -> str:
        """Đọc toàn bộ file text.

        Args:
            path: Đường dẫn file cần đọc.
            encoding: Bộ mã của file, mặc định UTF-8.

        Returns:
            Nội dung file dưới dạng chuỗi.

        Raises:
            FileNotFoundError: Khi file không tồn tại.
            UnicodeDecodeError: Khi file không đúng bộ mã chỉ định.
        """
        return Path(path).read_text(encoding=encoding)

    @staticmethod
    def write_text(path: PathLike, content: str, encoding: str = "utf-8") -> Path:
        """Ghi chuỗi vào file, tự tạo thư mục cha nếu chưa có.

        Args:
            path: Đường dẫn file đích.
            content: Nội dung cần ghi.
            encoding: Bộ mã khi ghi, mặc định UTF-8.

        Returns:
            Đường dẫn file đã ghi.
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding=encoding)
        return target

    @staticmethod
    def read_json(path: PathLike, encoding: str = "utf-8") -> Any:
        with Path(path).open("r", encoding=encoding) as f:
            return json.load(f)

    @staticmethod
    def write_json(
            path: PathLike,
            data: Any,
            encoding: str = "utf-8",
            indent: int = 2,
    ) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return target

    @staticmethod
    def list_files(
            history_dir: PathLike,
            pattern: str = "*",
            recursive: bool = False,
    ) -> list[Path]:
        """Liệt kê các file trong một thư mục.

        Args:
            history_dir: Đường dẫn thư mục cần liệt kê.
            pattern: Mẫu lọc tên file (glob), mặc định "*" (mọi file).
            recursive: Nếu True thì duyệt cả các thư mục con.

        Returns:
            Danh sách Path của các file (đã sắp xếp), bỏ qua thư mục con.

        Raises:
            FileNotFoundError: Khi thư mục không tồn tại.
            NotADirectoryError: Khi đường dẫn không phải là thư mục.
        """
        directory = Path(history_dir)
        if not directory.exists():
            raise FileNotFoundError(f"Thư mục không tồn tại: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(f"Đường dẫn không phải thư mục: {directory}")

        matches = directory.rglob(pattern) if recursive else directory.glob(pattern)
        return sorted(p for p in matches if p.is_file())
