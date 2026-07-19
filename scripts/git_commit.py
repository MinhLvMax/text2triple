from scripts.run_cmd_method import run
from datetime import datetime

import scripts.git_add
import scripts.git_status

msg = input('Commit: ')
if msg == '':
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    msg = f'Auto commit {timestamp}'

run('git', 'commit', '-m', msg)