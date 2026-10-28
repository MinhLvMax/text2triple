import requests
from pprint import pprint
import uuid

import pandas as pd

from src.old_code.helper_file import read_csv_to_df, write_dicts_to_csv
from src.old_code.config import Config


GRAPH_FODLER = Config.DATA_DIR / 'graphs'


def read_csv_to_dict(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    return df.to_dict(orient="records")


def add_uuid_column(path):
    '''Them cot uuid vao file csv'''
    df = read_csv_to_df(path)
    df.insert(0, "uuid", [str(uuid.uuid4()) for _ in range(len(df))])
    df.to_csv(path, index=False)


def dbpedia_entity_lookup(entity, max_results=5) -> list[dict]:
    '''Tim uri theo ten binh thuong'''
    params = {
        "query": entity,
        "format": "JSON",
        "maxResults": max_results
    }

    r = requests.get(
        "https://lookup.dbpedia.org/api/search",
        params=params
    )

    data = r.json()
    return data['docs']


# query = """
# PREFIX dbr: <http://dbpedia.org/resource/>
#
# SELECT ?s ?p ?o
# WHERE {
#     dbr:Nguyen_Hue ?p ?o
# }
# """
#
# url = "https://dbpedia.org/sparql"
#
# response = requests.get(
#     url,
#     params={
#         "query": query,
#         "format": "json"
#     },
#     headers={
#         "Accept": "application/sparql-results+json"
#     },
#     timeout=30
# )
#
# print("STATUS:", response.status_code)
# print("CONTENT-TYPE:", response.headers.get("Content-Type"))
# print("TEXT:", response.text[:1000])
#
# response.raise_for_status()
#
# data = response.json()
#
# FileHelper.write_json(
#     path=GRAPH_FODLER / 'nguyenhue.json',
#     data=data
# )

def main1():
    UUID_UNIQUE_ENTITIES_PATH = Config.DATA_DIR / 'uuid_unique_entities.csv'
    entities_dbpedia_candidates_path = Config.DATA_DIR / 'entities_dbpedia_candidates.csv'

    # Doc du lieu ra dict
    raws = read_csv_to_dict(
        path=UUID_UNIQUE_ENTITIES_PATH
    )

    # Tim uri lookup
    for r in raws:  # Duyẹt tung dong
        if r.get('lookup_status') == 'success':
            continue
        entity_name = r.get('entity')  # Lay ten thuc te de mang di tim kiem
        try:
            candidate_entities = dbpedia_entity_lookup(entity_name)  # Tim cac candicate theo ten

            if not candidate_entities:
                r['lookup_status'] = 'not_found'
                r['note'] = 'No DBpedia candidates found'

                write_dicts_to_csv(
                    data=raws,
                    path=UUID_UNIQUE_ENTITIES_PATH
                )
                continue

            for e in candidate_entities:  # Duyet tung candidate de them cac cot tu dict ban dau
                e['uuid'] = r['uuid']
                e['entity_lookup'] = r['entity']
                e['number_page'] = r['number_page']
                e['book_name'] = r['book_name']

                pprint(e)
            write_dicts_to_csv(  # luu ra file candicate
                data=candidate_entities,
                path=entities_dbpedia_candidates_path,
                mode='a'
            )
            r['lookup_status'] = 'success'  # Danh dau thanh cong
            r['note'] = ''  # Xoa note cu đi
            write_dicts_to_csv(data=raws, path=UUID_UNIQUE_ENTITIES_PATH)  # Update vao trong file

        except Exception as e:
            r['lookup_status'] = 'failed'  # Danh dau la that bai
            r['note'] = f'{type(e).__name__}: {e}'  # Them ghi chu
            write_dicts_to_csv(data=raws, path=UUID_UNIQUE_ENTITIES_PATH)  # Luu vao file
            continue

# ===



def entity_records():
    ...

def db_pedia_lookup(entity_name) -> dict:
    ...


def get_best_candicate():
    ...


def knowledge_enrichment():
    ...


def filter():
    ...


def graph_data():
    ...


def main():
    pass


if __name__ == '__main__':
    main1()
