import json
import logging
import re
from typing import Any, Dict, Optional

from neo4j import GraphDatabase

from src.application.port.base_graph_client import BaseGraphClient
from src.domain.extraction_schema.entities import BaseEntity
from src.domain.extraction_schema.extraction_result import ExtractionResult

logger = logging.getLogger(__name__)

_REL_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_LABEL_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def _safe_label(label: str) -> str:
    """Kiểm tra label PascalCase (Cypher không tham số hóa được label)."""
    if not _LABEL_RE.match(label):
        raise ValueError(f"Label không hợp lệ: {label!r}")
    return label


class Neo4jGraphClient(BaseGraphClient):
    """Adapter Neo4j cho BaseGraphClient.

    - Node: MERGE theo (label = type, name); label và relationship type được
      validate bằng regex vì Cypher không cho tham số hóa chúng.
    - Metadata (dict) được lưu dạng chuỗi JSON vì Neo4j không hỗ trợ map property.
    """

    def __init__(self, uri: str, user: str, password: str, database: Optional[str] = None):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def ingest_extraction_result(self, result: ExtractionResult) -> None:
        with self._driver.session(database=self._database) as session:
            session.execute_write(self._ingest_tx, result)

    def close(self) -> None:
        self._driver.close()

    @classmethod
    def _ingest_tx(cls, tx, result: ExtractionResult) -> None:
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
        return json.dumps(meta, ensure_ascii=False) if meta else None
