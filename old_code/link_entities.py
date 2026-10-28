from src.old_code.helper_db import get_table_names, get_table_columns, create_conn
from src.old_code.config import Config

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Entity(Base):
    __tablename__ = "entities"

    uuid: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    entity: Mapped[str | None] = mapped_column(String)
    entity_type: Mapped[str | None] = mapped_column(String)
    number_page: Mapped[str | None] = mapped_column(String)
    book_name: Mapped[str | None] = mapped_column(String)
    lookup_status: Mapped[str | None] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(String)

    # 1 Entity có nhiều EntityLookup
    lookups: Mapped[list["EntityLookup"]] = relationship(
        back_populates="entity"
    )


class EntityLookup(Base):
    __tablename__ = "entities_lookup"

    uuid: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    source_entity_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("entities.uuid")
    )

    score: Mapped[str | None] = mapped_column(String)
    refCount: Mapped[str | None] = mapped_column(String)
    resource: Mapped[str | None] = mapped_column(String)
    redirectlabel: Mapped[str | None] = mapped_column(String)
    typeName: Mapped[str | None] = mapped_column(String)
    comment: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)
    id: Mapped[str | None] = mapped_column(String)
    type: Mapped[str | None] = mapped_column(String)
    category: Mapped[str | None] = mapped_column(String)

    # EntityLookup thuộc về một Entity
    entity: Mapped["Entity"] = relationship(
        back_populates="lookups"
    )


# def dbpedia_entity_lookup(entity: Entity, max_results=5) -> list[DBpediaEntity]:
#     '''Tim uri theo ten binh thuong'''
#     params = {
#         "query": entity['entityName'],
#         "format": "JSON",
#         "maxResults": max_results
#     }
#     r = requests.get(
#         "https://lookup.dbpedia.org/api/search",
#         params=params
#     )
#     try:
#         data = r.json()
#     except requests.exceptions.JSONDecodeError:
#         raise
#     return [
#         {
#             'source_entity_id': entity['uuid'],
#             'uuid': create_new_uuid(),
#             **elookup,
#         }
#         for elookup in data['docs']
#     ]

def pipline():
    pass


if __name__ == '__main__':
    conn = create_conn(
        db_path=Config.DATA_DIR / 'data.db'
    )
    print(get_table_names(conn))
    print(get_table_columns(conn, 'entities'))
    print(get_table_columns(conn, 'entities_lookup'))

    pass
