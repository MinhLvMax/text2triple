import requests

# =========================
# 1. Tìm entity
# =========================

entity_name = "Việt Nam"

url = "https://lookup.dbpedia.org/api/search"

params = {
    "query": entity_name,
    "format": "JSON",
    "maxResults": 5
}

response = requests.get(url, params=params, timeout=15)
response.raise_for_status()

data = response.json()

print("=== ENTITY LINKING ===")

for i, item in enumerate(data["docs"]):
    print(f"\n[{i}]")
    print("Label:", item.get("label"))
    print("Resource:", item.get("resource"))
    print("Score:", item.get("score"))


# =========================
# 2. Lấy quan hệ xung quanh
# =========================

uri = data["docs"][0]["resource"][0]

print("\n\n=== ENTITY ===")
print(uri)

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
LIMIT 50
"""

sparql_url = "https://dbpedia.org/sparql"

response = requests.get(
    sparql_url,
    params={
        "query": query,
        "format": "json"
    },
    timeout=30
)

response.raise_for_status()

data = response.json()

print("\n=== RELATIONSHIPS ===")

for item in data["results"]["bindings"]:
    subject = item["s"]["value"]
    predicate = item["p"]["value"]
    object_ = item["o"]["value"]

    print("\nSUBJECT :", subject)
    print("PREDICATE:", predicate)
    print("OBJECT  :", object_)