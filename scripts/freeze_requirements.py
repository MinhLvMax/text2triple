from scripts.run_cmd_method import run
from scripts.config import PROJECT_PATH

requirements = PROJECT_PATH / 'requirements.txt'

with requirements.open('w', encoding='utf-8') as f:
    run('python', '-m', 'pip', 'freeze', stdout=f)