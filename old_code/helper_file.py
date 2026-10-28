import json
from pathlib import Path
from typing import Any, Union, Literal
import csv

import pandas as pd

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


def read_json(path: PathLike, encoding: str = "utf-8") -> Any:
    with Path(path).open("r", encoding=encoding) as f:
        return json.load(f)


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


def read_csv_to_df(path):
    return pd.read_csv(
        path,
        encoding="utf-8-sig"
    )


def read_csv_to_list_dict(
        path: str,  # Đường dẫn tới file CSV cần đọc
) -> list[dict]:
    """Đọc file CSV và trả về danh sách các dict."""

    with open(  # Mở file CSV để đọc
            path,  # Sử dụng trực tiếp đường dẫn file
            "r",  # Mở file ở chế độ đọc
            encoding="utf-8-sig",  # Hỗ trợ UTF-8 có BOM
            newline="",  # Giữ nguyên newline để csv xử lý đúng
    ) as f:
        reader = csv.DictReader(f)  # Đọc CSV và chuyển mỗi dòng thành dict
        data = list(reader)  # Chuyển toàn bộ dữ liệu thành list[dict]

    return data  # Trả về danh sách các dict


def write_dicts_to_csv(
        data: list[dict],
        path,
        mode: Literal["w", "a"] = "w"
):
    """Lưu list dict ra CSV."""

    if not data:
        return

    fieldnames = data[0].keys()

    with open(
            path,
            mode,
            newline="",
            encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        # Chỉ ghi header khi ghi mới
        if mode == "w":
            writer.writeheader()

        writer.writerows(data)


def add_column_to_csv(path, column_name, value):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df[column_name] = value

    df.to_csv(
        path,
        index=False,
        encoding="utf-8-sig"
    )


def delete_columns_in_csv(input_path, columns_to_delete):
    '''Xoa cot du tra ve file moi'''
    input_path = Path(input_path)
    df = pd.read_csv(input_path, encoding="utf-8-sig")

    # Xóa các cột được chỉ định
    df.drop(columns=columns_to_delete, inplace=True, errors="ignore")

    # Tạo tên file mới với hậu tố _delete
    output_path = input_path.with_name(
        f"{input_path.stem}_delete{input_path.suffix}"
    )

    # Lưu file
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    return str(output_path)


def normalize_entity(text: str) -> str:
    text = text.strip().lower()

    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )
    return text


if __name__ == '__main__':
    print(normalize_entity('Lâm Văn Minh'))
