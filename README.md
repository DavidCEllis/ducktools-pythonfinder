# ducktools: pythonfinder #

Find python installs on Linux, Windows and MacOS.

Attempts to find python installed by `pyenv`, system python or python installs
correctly registered on Windows.

Usage:

```python
import os.path
from ducktools.pythonfinder import get_python_installs

user_path = os.path.expanduser("~")

for install in get_python_installs():
    install.executable = os.path.relpath(install.executable, user_path)
    print(install)
```

Example Windows Output:

```
PythonInstall(version=(3, 12, 1), executable='.pyenv\\pyenv-win\\versions\\3.12.1\\python.exe', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 12, 1), executable='.pyenv\\pyenv-win\\versions\\3.12.1-win32\\python.exe', architecture='32bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 11, 7), executable='.pyenv\\pyenv-win\\versions\\3.11.7\\python.exe', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 10, 11), executable='.pyenv\\pyenv-win\\versions\\3.10.11\\python.exe', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 9, 13), executable='.pyenv\\pyenv-win\\versions\\3.9.13\\python.exe', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 8, 10), executable='.pyenv\\pyenv-win\\versions\\3.8.10\\python.exe', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 12, 1), executable='AppData\\Local\\Programs\\Python\\Python312\\python.exe', architecture='64bit', implementation='cpython', metadata={...})
```
