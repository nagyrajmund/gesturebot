import sys
import subprocess

commands = ["-m pip install -r gesticulator/requirements.txt --use-deprecated=legacy-resolver",
            "-m pip install -e .",
            "-m pip install -e gesticulator/visualization"] 

for cmd in commands:
    subprocess.check_call([sys.executable] + cmd.split())