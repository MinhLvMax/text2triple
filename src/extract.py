from src import helper
import json
import uuid
from src.groq_llm_services import GroqServices

data = helper.read_text('chunk_test.txt')
prompt = helper.read_text('nouns_extract.txt', text=data)
groq_services = GroqServices()
result = groq_services.chat(prompt, json_mode=True)
result_json = json.loads(result.content)
result_json['nouns'] = [{
    'id': str(uuid.uuid4()),
    'name': n,
} for n in result_json['nouns']]

helper.json_save('data.json', result_json)
