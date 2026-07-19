from scripts.run_method import run
from datetime import datetime

run('git', 'add', '.')
import scripts.git_status

msg = input('Commit: ')
if msg == '':
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    msg = f'Auto commit {timestamp}'

run('git', 'commit', '-m', msg)