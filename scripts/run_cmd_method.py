from pathlib import Path
import subprocess
from scripts.config import PROJECT_PATH

def run(*command, workdir=PROJECT_PATH, **kwargs):
    return subprocess.run(
        [str(c) for c in command],
        cwd=Path(workdir),
        text=True,
        check=False,
        **kwargs,
    )