# ducktools: pythonfinder #

Find python installs on Linux, Windows and MacOS.

## Quick usage ##

`python -m ducktools.pythonfinder` will provide a table of installed python versions 
and their respective folders.

## Why? ##

For the purposes of PEP723 script dependencies it may be useful to find another version
of python other than the one currently running in order to satisfy the `requires-python`
field. This tool is intended to search for potential python installs to attempt to
satisfy such a requirement.

## Currently Finds ##

On Linux and MacOS:
* pyenv based installs in $PYENV_ROOT
* 'python' binaries on $PATH
  * This will find the *first* 'python' and 'pythonX.Y' on path in the same way
    as calling them in the shell would.

On Windows:
* Python versions recorded in the registry as in PEP 514 (with additional metadata)
  * If a pyenv install is done with -r / --register it will be listed with metadata
* pyenv-win installs in %PYENV_ROOT%


## Module usage ##

Usage:

```python
import os.path
from ducktools.pythonfinder import get_python_installs

user_path = os.path.expanduser("~")

for install in get_python_installs():
    install.executable = install.executable.replace(user_path, "~")
    print(install)
```

Example Windows Output:

```
PythonInstall(version=(3, 12, 1, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.12.1\\python.exe', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 12, 1, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.12.1-win32\\python.exe', architecture='32bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 12, 1, 'final', 0), executable='~\\AppData\\Local\\Programs\\Python\\Python312\\python.exe', architecture='64bit', implementation='cpython', metadata={...})
PythonInstall(version=(3, 11, 7, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.11.7\\python.exe', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 10, 11, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.10.11\\python.exe', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 9, 13, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.9.13\\python.exe', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 8, 10, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.8.10\\python.exe', architecture='64bit', implementation='cpython', metadata={})
```

Example Linux Output:

```
PythonInstall(version=(3, 12, 1, 'final', 0), executable='~/.pyenv/versions/3.12.1/bin/python', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 12, 0, 'final', 0), executable='~/.pyenv/versions/3.12.0/bin/python', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 11, 6, 'final', 0), executable='~/.pyenv/versions/3.11.6/bin/python', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 10, 13, 'final', 0), executable='~/.pyenv/versions/3.10.13/bin/python', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 10, 12, 'final', 0), executable='/usr/bin/python3.10', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 10, 12, 'final', 0), executable='/usr/bin/python3', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 10, 12, 'final', 0), executable='~/.pyenv/versions/pypy3.10-7.3.12/bin/python', architecture='64bit', implementation='pypy', metadata={'pypy_version': '7.3.12'})
PythonInstall(version=(3, 9, 18, 'final', 0), executable='~/.pyenv/versions/3.9.18/bin/python', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 8, 18, 'final', 0), executable='~/.pyenv/versions/3.8.18/bin/python', architecture='64bit', implementation='cpython', metadata={})
PythonInstall(version=(3, 5, 2, 'final', 0), executable='/usr/bin/python3.5', architecture='64bit', implementation='cpython', metadata={})
```
