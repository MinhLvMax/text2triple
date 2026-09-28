import sqlite3
from typing import Any


class EntitiesLookupRepository:
    """Repository thao tác với bảng entities_lookup."""

    def __init__(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Khởi tạo repository."""

        self.conn = conn

    def get_all(self) -> list[dict[str, Any]]:
        """Lấy toàn bộ record."""

        cursor = self.conn.execute(
            'SELECT * FROM "entities_lookup"'
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
            'SELECT * FROM "entities_lookup" '
            'WHERE "uuid" = ?',
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
            f'"{column}"'
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
            f'INSERT INTO "entities_lookup" '
            f'({column_names}) '
            f'VALUES ({placeholders})',
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
            f'"{column}" = ?'
            for column in data
        )

        values = tuple(
            data[column]
            for column in data
        )

        values += (id_value,)

        self.conn.execute(
            f'UPDATE "entities_lookup" '
            f'SET {assignments} '
            f'WHERE "uuid" = ?',
            values,
        )

        self.conn.commit()

    def delete(
        self,
        id_value: Any,
    ) -> None:
        """Xóa một record."""

        self.conn.execute(
            f'DELETE FROM "entities_lookup" '
            f'WHERE "uuid" = ?',
            (id_value,),
        )

        self.conn.commit()
