"""Adapter kết nối và thao tác với cơ sở dữ liệu đồ thị Neo4j."""
import json
import logging
import re
from typing import Any, Dict, Optional

from neo4j import GraphDatabase

from src.application.port.base_graph_client import BaseGraphClient
from src.domain.extraction_schema.entities import BaseEntity
from src.domain.extraction_schema.extraction_result import ExtractionResult

logger = logging.getLogger(__name__)

# Biểu thức chính quy kiểm thực tính an toàn của tên quan hệ và nhãn Node
_REL_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_LABEL_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def _safe_label(label: str) -> str:
    """Kiểm tra nhãn theo chuẩn PascalCase nhằm ngăn ngừa injection do Cypher không hỗ trợ tham số hóa label."""
    if not _LABEL_RE.match(label):
        raise ValueError(f"Label không hợp lệ: {label!r}")
    return label


class Neo4jGraphClient(BaseGraphClient):
    """Adapter triển khai BaseGraphClient tương tác với Neo4j thông qua Bolt Protocol.

    Quy ước lưu trữ:
    - Node: Thực hiện MERGE theo cặp (Label = type, name). Nhãn và loại quan hệ được kiểm thực
      qua Regex do ngôn ngữ Cypher không hỗ trợ tham số hóa nhãn động.
    - Metadata: Tuần tự hóa dictionary thành chuỗi JSON do thuộc tính dạng Map không được Neo4j hỗ trợ lưu trực tiếp.
    """

    def __init__(self, uri: str, user: str, password: str, database: Optional[str] = None):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def ingest_extraction_result(self, result: ExtractionResult) -> None:
        """Thực thi giao dịch ghi (Write Transaction) nạp kết quả trích xuất vào Neo4j."""
        with self._driver.session(database=self._database) as session:
            session.execute_write(self._ingest_tx, result)

    def close(self) -> None:
        """Đóng kết nối driver của Neo4j."""
        self._driver.close()

    @classmethod
    def _ingest_tx(cls, tx, result: ExtractionResult) -> None:
        """Giao dịch nội bộ thực thi câu lệnh MERGE cho từng bộ ba (Triple) cùng chứng cứ."""
        for rel in result.relations:
            src: BaseEntity = rel.domain
            dst: BaseEntity = rel.range
            rel_type = rel.relation_name
            if not _REL_TYPE_RE.match(rel_type):
                raise ValueError(f"Tên quan hệ không hợp lệ: {rel_type!r}")

            query = (
                f"MERGE (a:{_safe_label(src.type)} {{name: $src_name}}) "
                "ON CREATE SET a.description = $src_desc "
                "SET a.metadata = coalesce($src_meta, a.metadata) "
                f"MERGE (b:{_safe_label(dst.type)} {{name: $dst_name}}) "
                "ON CREATE SET b.description = $dst_desc "
                "SET b.metadata = coalesce($dst_meta, b.metadata) "
                f"MERGE (a)-[r:{rel_type} {{chunk_id: $chunk_id, evidence: $evidence}}]->(b) "
                "SET r.metadata = $rel_meta"
            )
            tx.run(
                query,
                src_name=src.name,
                src_desc=src.description,
                src_meta=cls._dump_meta(src.metadata),
                dst_name=dst.name,
                dst_desc=dst.description,
                dst_meta=cls._dump_meta(dst.metadata),
                chunk_id=result.chunk_id,
                evidence=rel.evidence,
                rel_meta=cls._dump_meta(rel.metadata) or "{}",
            )
        logger.info("Đã ghi %d quan hệ của chunk %s vào Neo4j.", len(result.relations), result.chunk_id)

    @staticmethod
    def _dump_meta(meta: Dict[str, Any]) -> Optional[str]:
        """Tuần tự hóa metadata thành chuỗi JSON hỗ trợ tiếng Việt có dấu."""
        return json.dumps(meta, ensure_ascii=False) if meta else None
