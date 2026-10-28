import sqlite3
from typing import TypedDict, NotRequired

import requests
from src.old_code.helper_db import create_conn, create_or_insert, create_new_uuid
from src.old_code.repositories.entities_repository import EntitiesRepository


class Entity(TypedDict):
    uuid: str
    entityName: str
    numberPage: NotRequired[int]
    entityType: NotRequired[int]
    bookName: NotRequired[int]


class DBpediaEntity(TypedDict):
    uuid: str
    source_entity_id: str
    category: list[str]
    id: list[str]
    label: list[str]
    redirectlabel: list[str]
    refCount: list[str]
    resource: list[str]
    score: list[str]
    type: list[str]
    typeName: list[str]


class EntityWithDBpedia(Entity, DBpediaEntity):
    pass


class Triple(TypedDict):
    subject: str
    predicate: str
    object: str
    direction: str


class KnowledgeEnrichment(TypedDict):
    entityUri: str
    triples: list[Triple]


# def entity_record(path: str) -> list[Entity]:
#     df = read_csv_to_df(path)
#     entities: list[Entity] = []
#     for _, row in df.iterrows():
#         entity: Entity = {
#             "entityName": row["entity"],
#             "numberPage": int(row["number_page"]),
#             "bookName": row["book_name"],
#             'entityType': row['entity_type']
#         }
#         entities.append(entity)
#     return entities


def dbpedia_entity_lookup(entity: Entity, max_results=5) -> list[DBpediaEntity]:
    '''Tim uri theo ten binh thuong'''
    params = {
        "query": entity['entityName'],
        "format": "JSON",
        "maxResults": max_results
    }
    r = requests.get(
        "https://lookup.dbpedia.org/api/search",
        params=params
    )
    try:
        data = r.json()
    except requests.exceptions.JSONDecodeError:
        raise
    return [
        {
            'source_entity_id': entity['uuid'],
            'uuid': create_new_uuid(),
            **elookup,
        }
        for elookup in data['docs']
    ]


def get_best_candidate(candidates: list[DBpediaEntity]) -> DBpediaEntity:
    # Lấy theo score cao nhất
    return max(candidates, key=lambda x: float(x["score"][0]))


def linked_entity(
        entity: Entity,
        dBpediaEntity: DBpediaEntity
) -> EntityWithDBpedia:
    return {
        **entity,
        **dBpediaEntity,
    }


def get_knowledge_enrichment(dBpediaEntity: DBpediaEntity):
    uri = dBpediaEntity["resource"][0]  # Lay uri

    # Viet query
    query = f"""
    SELECT ?s ?p ?o
    WHERE {{
        {{
            <{uri}> ?p ?o .
            BIND(<{uri}> AS ?s)
        }}
        UNION
        {{
            ?s ?p <{uri}> .
            BIND(<{uri}> AS ?o)
        }}
    }}
    LIMIT 100
    """

    # truy van
    response = requests.get(
        "https://dbpedia.org/sparql",
        params={
            "query": query,
            "format": "json"
        },
        timeout=30
    )

    response.raise_for_status()  # cho truy van xong

    data = response.json()
    return data
    triples: list[Triple] = []

    for binding in data["results"]["bindings"]:
        subject = binding["s"]["value"]
        predicate = binding["p"]["value"]
        object_ = binding["o"]["value"]

        direction = (
            "outgoing"
            if subject == uri
            else "incoming"
        )

        triples.append({
            "subject": subject,
            "predicate": predicate,
            "object": object_,
            "direction": direction
        })

    return {
        "entityUri": uri,
        "triples": triples
    }


def has_been_looked_up(ent_rep, entity: Entity):
    status = ent_rep.get_by_id(entity['uuid'])['lookup_status']
    return status == 'success'


def insert_lookup(conn, entities_lookup):
    create_or_insert(
        conn,
        'entities_lookup',
        data=entities_lookup,
        primary_key='uuid',
        foreign_key='source_entity_id',
        foreign_table='entities',
        reference_key='uuid'
    )


def marked_as_searched(ent_rep, entity):
    ent_rep.update(
        id_value=entity['uuid'],
        data={
            'lookup_status': 'success'
        }
    )


def get_fail_and_pending_entities(conn: sqlite3.Connection):
    cursor = conn.execute(
        '''
SELECT * 
FROM entities
WHERE lookup_status != 'success'            
        '''
    )

    columns = [
        description[0]
        for description in cursor.description
    ]

    # print(cursor.fetchall()) # có ra dữ liệu list tup

    # print(
    #     [
    #         dict(zip(columns, row))
    #         for row in cursor.fetchall()
    #     ]
    # )

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def test_get_fail_and_pending_entities():
    from src.old_code.config import Config

    db_path = Config.DATA_DIR / 'data.db'  # Đường dẫn db

    conn = create_conn(  # Khai báo connection db
        db_path=db_path
    )
    get_fail_and_pending_entities(conn)


def run_pipline():
    print(run_pipline.__name__)
    from src.old_code.config import Config

    db_path = Config.DATA_DIR / 'data.db'  # Đường dẫn db
    conn = create_conn(  # Khai báo connection db
        db_path=db_path
    )

    ent_rep = EntitiesRepository(conn)  # Khai báo repo
    entities = get_fail_and_pending_entities(conn)  # Lấy danh sách tất cả thực thể chưa được cào dữ liệu thành công
    process_len = len(entities)
    for i, row in enumerate(entities):

        print(f'{i} / {process_len}')
        entity: Entity = {
            'uuid': row['uuid'],
            'entityName': row['entity']
        }
        # Kiểm tra trạng thái lookup, nếu success rồi thì continue
        if has_been_looked_up(ent_rep, entity):
            print(f'Da lookup {entity['entityName']} bo qua')
            continue
        print(f'Looking up {entity['entityName']}')
        # Tìm các lookup của pipline

        try:
            entities_lookup = dbpedia_entity_lookup(entity)
            # insert lookup vào csdl
            insert_lookup(conn, entities_lookup)

            # Dánh dấu đã search
            marked_as_searched(ent_rep, entity)
        except requests.exceptions.JSONDecodeError as e:
            ent_rep.update(
                entity['uuid'],
                {
                    'note': str(e),
                    'lookup_status': 'failed'
                }
            )


if __name__ == '__main__':
    run_pipline()

    # test_get_fail_and_pending_entities()
    ...
