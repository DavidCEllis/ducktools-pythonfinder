# ducktools: pythonfinder #

Find python installs on Linux, Windows and MacOS.

Requires Python >= 3.10 (but will discover older Python installs)

## Quick usage ##

`python -m ducktools.pythonfinder` will provide a table of installed python versions
and their respective folders. It will also indicate the python running the
command if it is found, or the python that is the base for the venv running the command.

Python versions listed can be restricted by using the `--max`, `--min` and
`--exact` options to the command.

The module provides two main functions:

* `get_python_installs` is a generator that will yield each python version it discovers
* `list_python_installs` will take the python versions discovered by `get_python_installs`
  and return a sorted list from newest to oldest python version discovered.

On Windows these methods will search the registry for PEP514 recorded python installs
before checking for any `pyenv-win` installs that have not been registered.

On Linux and MacOS this will search for `pyenv` installs first and then for any
`python*` binaries found on `path`. For those found on `path` they will be made
to run a small script to identify the version.

The python installs will be returned as instances of `PythonInstall` which will
contain version info and executable path along with some other useful metadata.

## Why? ##

For the purposes of PEP723 script dependencies it may be useful to find another version
of python other than the one currently running in order to satisfy the `requires-python`
field. This tool is intended to search for potential python installs to attempt to
satisfy such a requirement.

## Isn't there already a 'pythonfinder' module? ##

That module appears to require searching for a specific version and will find venv pythons.

In contrast `ducktools.pythonfinder` simply yields python installs as they are discovered
and will attempt to avoid returning virtualenv python installs

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
