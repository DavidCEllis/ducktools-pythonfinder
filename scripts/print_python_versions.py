import os.path
from ducktools.pythonfinder import get_python_installs

user_path = os.path.expanduser("~")

for env in get_python_installs():
    env.executable = env.executable.replace(user_path, "~")
    print(env)
