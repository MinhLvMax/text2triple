import sqlite3
from pathlib import Path
import uuid
from typing import Any


def create_new_uuid() -> str:
    random_uuid = str(uuid.uuid4())
    return random_uuid


TYPE_MAP = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
    bool: "INTEGER",
    type(None): "TEXT"
}


def create_conn(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def create_or_insert(
        conn: sqlite3.Connection,  # Connection tới SQLite
        table_name: str,  # Tên bảng cần tạo
        data: list[dict],  # nhiều dict bản ghi
        primary_key: str | None = None,  # Tên cột khóa chính
        foreign_key: str | None = None,  # Tên cột khóa ngoại
        foreign_table: str | None = None,  # Tên bảng được tham chiếu
        reference_key: str | None = None  # Tên cột được tham chiếu
) -> None:
    """Tự tạo bảng dựa trên data và insert một hoặc nhiều bản ghi."""

    # Kiểm tra data phải là list chứa các dict
    if not isinstance(data, list) or not all(
            isinstance(row, dict) for row in data
    ):
        raise TypeError("data phải là dict hoặc list[dict]")

    # Nếu danh sách rỗng thì không thực hiện gì
    if not data:
        return

    # Dictionary lưu tên column và kiểu SQLite tương ứng
    columns_type: dict[str, str] = {}

    # Duyệt qua toàn bộ các record
    for row in data:

        # Duyệt qua từng column và value
        for key, value in row.items():

            # None không đủ thông tin để xác định kiểu dữ liệu
            if value is None:
                continue

            # Lấy kiểu SQLite từ kiểu Python
            sql_type = TYPE_MAP.get(type(value), "TEXT")

            # Nếu column chưa có kiểu thì sử dụng kiểu hiện tại
            if key not in columns_type:
                columns_type[key] = sql_type

    # Những column chỉ chứa None sẽ mặc định là TEXT
    for row in data:
        for key in row:
            # Kiểm tra column chưa được xác định kiểu
            if key not in columns_type:
                columns_type[key] = "TEXT"

    # Danh sách câu lệnh định nghĩa column
    columns: list[str] = []

    # Duyệt qua từng column
    for key, sql_type in columns_type.items():

        # Tạo định nghĩa column
        column = f'"{key}" {sql_type}'

        # Nếu column là khóa chính thì thêm PRIMARY KEY
        if key == primary_key:
            column += " PRIMARY KEY"

        # Thêm column vào danh sách
        columns.append(column)

    # Kiểm tra thông tin khóa ngoại có đầy đủ hay không
    if foreign_key and foreign_table and reference_key:
        # Thêm FOREIGN KEY vào bảng
        columns.append(
            f'FOREIGN KEY ("{foreign_key}") '
            f'REFERENCES "{foreign_table}" ("{reference_key}")'
        )

    # Tạo câu SQL CREATE TABLE
    create_sql: str = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {", ".join(columns)}
        )
    '''

    # Thực thi CREATE TABLE
    conn.execute(create_sql)

    # Lấy danh sách tên column
    keys: list[str] = list(columns_type.keys())

    # Tạo danh sách tên column cho INSERT
    column_names: str = ", ".join(
        f'"{key}"' for key in keys
    )

    # Tạo placeholder tương ứng với số column
    placeholders: str = ", ".join(
        "?" for _ in keys
    )

    # Tạo câu SQL INSERT
    insert_sql: str = f'''
        INSERT INTO "{table_name}" ({column_names})
        VALUES ({placeholders})
    '''

    # Chuyển list[dict] thành list[tuple]
    values: list[tuple] = [
        tuple(
            str(row.get(key)) if isinstance(row.get(key), list) else row.get(key)
            for key in keys
        )
        for row in data
    ]

    # Insert toàn bộ record cùng lúc
    conn.executemany(insert_sql, values)

    # Lưu thay đổi vào database
    conn.commit()


def drop_columns(
        db_path: str,
        table_name: str,
        columns: str | list[str]
) -> None:
    if isinstance(columns, str):
        columns = [columns]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        for column in columns:
            cursor.execute(
                f'ALTER TABLE "{table_name}" DROP COLUMN "{column}"'
            )
        conn.commit()


def add_column(
        db_path: str,
        table_name: str,
        column_name: str,
        default_value=None
) -> None:
    column_type = TYPE_MAP[type(default_value)]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        if default_value is None:
            sql = f'''
                ALTER TABLE "{table_name}"
                ADD COLUMN "{column_name}" {column_type}
            '''
            cursor.execute(sql)

        else:
            sql = f'''
                ALTER TABLE "{table_name}"
                ADD COLUMN "{column_name}" {column_type}
                DEFAULT ?
            '''
            cursor.execute(sql, (default_value,))

        conn.commit()


def read_table_to_list_dict(
        conn: sqlite3.Connection,  # Connection tới SQLite database
        table_name: str,  # Tên bảng cần đọc
) -> list[dict]:
    """Đọc toàn bộ một bảng SQLite và trả về list[dict]."""

    cursor = conn.execute(  # Thực thi câu SQL để lấy toàn bộ dữ liệu
        f'SELECT * FROM "{table_name}"'
    )

    columns = [  # Lấy tên các cột từ kết quả truy vấn
        description[0]
        for description in cursor.description
    ]

    rows = cursor.fetchall()  # Lấy toàn bộ các dòng dữ liệu

    data = [  # Chuyển từng dòng thành một dict
        dict(zip(columns, row))
        for row in rows
    ]

    return data  # Trả về danh sách các dict



def get_table_names(
    conn: sqlite3.Connection,  # Connection tới SQLite database
) -> list[str]:
    """Lấy danh sách tên các bảng trong database."""

    rows = conn.execute(  # Thực thi truy vấn lấy tên bảng
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    return [  # Trả về danh sách tên bảng
        row[0]
        for row in rows
    ]


def get_table_columns(
    conn: sqlite3.Connection,  # Connection tới SQLite database
    table_name: str,  # Tên bảng cần lấy schema
) -> list[dict[str, Any]]:
    """Lấy thông tin các column của một bảng."""

    rows = conn.execute(  # Lấy schema của bảng từ SQLite
        f'PRAGMA table_info("{table_name}")'
    ).fetchall()

    return [  # Chuyển schema thành list[dict]
        {
            "cid": row[0],
            "name": row[1],
            "type": row[2],
            "notnull": row[3],
            "default": row[4],
            "primary_key": row[5],
        }
        for row in rows
    ]


def generate_repository_code(
    table_name: str,  # Tên bảng cần tạo repository
    columns: list[dict[str, Any]],  # Thông tin các column của bảng
) -> str:
    """Sinh source code Python cho một repository."""

    class_name = "".join(  # Chuyển tên bảng thành tên class
        word.capitalize()
        for word in table_name.split("_")
    ) + "Repository"

    primary_key = next(  # Tìm column khóa chính đầu tiên
        (
            column["name"]
            for column in columns
            if column["primary_key"]
        ),
        "id",
    )

    return f'''\
import sqlite3
from typing import Any


class {class_name}:
    """Repository thao tác với bảng {table_name}."""

    def __init__(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Khởi tạo repository."""

        self.conn = conn

    def get_all(self) -> list[dict[str, Any]]:
        """Lấy toàn bộ record."""

        cursor = self.conn.execute(
            'SELECT * FROM "{table_name}"'
        )

        columns = [
            description[0]
            for description in cursor.description
        ]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def get_by_id(
        self,
        id_value: Any,
    ) -> dict[str, Any] | None:
        """Lấy một record theo khóa chính."""

        cursor = self.conn.execute(
            'SELECT * FROM "{table_name}" '
            'WHERE "{primary_key}" = ?',
            (id_value,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [
            description[0]
            for description in cursor.description
        ]

        return dict(zip(columns, row))

    def insert(
        self,
        data: dict[str, Any],
    ) -> None:
        """Thêm một record."""

        columns = list(data.keys())

        column_names = ", ".join(
            f'"{{column}}"'
            for column in columns
        )

        placeholders = ", ".join(
            "?"
            for _ in columns
        )

        values = tuple(
            data[column]
            for column in columns
        )

        self.conn.execute(
            f'INSERT INTO "{table_name}" '
            f'({{column_names}}) '
            f'VALUES ({{placeholders}})',
            values,
        )

        self.conn.commit()

    def update(
        self,
        id_value: Any,
        data: dict[str, Any],
    ) -> None:
        """Cập nhật một record."""

        assignments = ", ".join(
            f'"{{column}}" = ?'
            for column in data
        )

        values = tuple(
            data[column]
            for column in data
        )

        values += (id_value,)

        self.conn.execute(
            f'UPDATE "{table_name}" '
            f'SET {{assignments}} '
            f'WHERE "{primary_key}" = ?',
            values,
        )

        self.conn.commit()

    def delete(
        self,
        id_value: Any,
    ) -> None:
        """Xóa một record."""

        self.conn.execute(
            f'DELETE FROM "{table_name}" '
            f'WHERE "{primary_key}" = ?',
            (id_value,),
        )

        self.conn.commit()
'''


def write_repository_file(
    output_folder: str,  # Thư mục chứa repository
    table_name: str,  # Tên bảng
    code: str,  # Source code repository cần ghi
) -> None:
    """Ghi source code repository ra file Python."""

    output_path = Path(output_folder)  # Chuyển output thành Path

    output_path.mkdir(  # Tạo thư mục nếu chưa tồn tại
        parents=True,
        exist_ok=True,
    )

    file_path = output_path / (  # Tạo đường dẫn file repository
        f"{table_name.lower()}_repository.py"
    )

    file_path.write_text(  # Ghi source code vào file
        code,
        encoding="utf-8",
    )


def build_repositories(
    db_path: str,  # Đường dẫn tới file SQLite database
    output_folder: str,  # Thư mục chứa các file repository
) -> None:
    """Sinh repository Python cho từng bảng SQLite."""

    conn = sqlite3.connect(db_path)  # Kết nối tới database

    try:
        tables = get_table_names(conn)  # Lấy danh sách các bảng

        for table_name in tables:  # Duyệt qua từng bảng
            columns = get_table_columns(  # Lấy schema của bảng
                conn,
                table_name,
            )

            code = generate_repository_code(  # Sinh source code repository
                table_name,
                columns,
            )

            write_repository_file(  # Ghi repository ra file
                output_folder,
                table_name,
                code,
            )

    finally:
        conn.close()  # Đảm bảo connection luôn được đóng


if __name__ == '__main__':
    pass
    # build_repositories(
    #     db_path=r'D:\projects\text2triple\data\data.db',
    #     output_folder=Config.PROJECT_DIR / 'src' / 'repositories'
    # )

