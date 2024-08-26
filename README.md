# ducktools: pythonfinder #

Find local python installs on Windows/Linux/MacOS and find the latest installers from python.org
for Windows and MacOS or sources for Linux (as python.org does not provide linux installers).

Requires Python >= 3.8 (but will discover older Python installs)

## Command Line Usage ##

`ducktools-pythonfinder` can be used as a module or as a bundled zipapp (as `pythonfinder.pyz`).

`python pythonfinder.pyz` or `python -m ducktools.pythonfinder` 
will provide a table of installed python versions
and their respective folders. It will also indicate the python running the
command if it is found, or the python that is the base for the venv running the command.

Python versions listed can be restricted by using the `--max`, `--min` and
`--compatible` options to the command. These roughly translate to `>=` for min, `<` for max
and `~=` for compatible in python version specifiers.

If you wish to find the latest binaries available from python.org for your platform 
(or sources on Linux) there is the additional `online` command with some extra flags.

By default it will fetch the latest patches for each Python release (eg: 2.7.18 for 2.7) for 
the hardware you're on. The filters for local versions also work.

* `--all-binaries` will get you all binary releases that match the restrictions.
* `--system` and `--machine` allow you to specify a platform other than the one you are using
  (the values you give should match platform.system() and platform.machine() return values).
* `--prerelease` includes prerelease versions in the search.

Example: 
`python pythonfinder.pyz online --min 3.10 --system Windows --machine AMD64`

```
| Python Version | URL                                                                |
| -------------- | ------------------------------------------------------------------ |
|         3.12.5 | https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe   |
|         3.11.9 | https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe   |
|        3.10.11 | https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe |
```

## Library Usage ##

### Local installs ###

The module provides two main functions for searching for local python installs:

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

Example:

```python
import os.path
from ducktools.pythonfinder import list_python_installs

user_path = os.path.expanduser("~")

for install in list_python_installs():
    install.executable = install.executable.replace(user_path, "~")
    print(install)
```

Example Windows Output:

```
PythonInstall(version=(3, 12, 5, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.12.5\\python.exe', architecture='64bit', implementation='cpython', metadata={'DiplayName': 'Python 3.12 (64-bit)', 'SupportUrl': 'https://github.com/pyenv-win/pyenv-win/issues', 'SysArchitecture': '64bit', 'SysVersion': '3.12', 'Version': '3.12.5', 'InWindowsRegistry': True}, shadowed=False)
PythonInstall(version=(3, 12, 3, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.12.3\\python.exe', architecture='64bit', implementation='cpython', metadata={}, shadowed=False)
PythonInstall(version=(3, 11, 9, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.11.9\\python.exe', architecture='64bit', implementation='cpython', metadata={'DiplayName': 'Python 3.11 (64-bit)', 'SupportUrl': 'https://github.com/pyenv-win/pyenv-win/issues', 'SysArchitecture': '64bit', 'SysVersion': '3.11', 'Version': '3.11.9', 'InWindowsRegistry': True}, shadowed=False)
PythonInstall(version=(3, 10, 11, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.10.11\\python.exe', architecture='64bit', implementation='cpython', metadata={'DiplayName': 'Python 3.10 (64-bit)', 'SupportUrl': 'https://github.com/pyenv-win/pyenv-win/issues', 'SysArchitecture': '64bit', 'SysVersion': '3.10', 'Version': '3.10.11', 'InWindowsRegistry': True}, shadowed=False)
PythonInstall(version=(3, 9, 13, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.9.13\\python.exe', architecture='64bit', implementation='cpython', metadata={'DiplayName': 'Python 3.9 (64-bit)', 'SupportUrl': 'https://github.com/pyenv-win/pyenv-win/issues', 'SysArchitecture': '64bit', 'SysVersion': '3.9', 'Version': '3.9.13', 'InWindowsRegistry': True}, shadowed=False)
PythonInstall(version=(3, 8, 10, 'final', 0), executable='~\\.pyenv\\pyenv-win\\versions\\3.8.10\\python.exe', architecture='64bit', implementation='cpython', metadata={'DiplayName': 'Python 3.8 (64-bit)', 'SupportUrl': 'https://github.com/pyenv-win/pyenv-win/issues', 'SysArchitecture': '64bit', 'SysVersion': '3.8', 'Version': '3.8.10', 'InWindowsRegistry': True}, shadowed=False)
PythonInstall(version=(3, 13, 0, 'candidate', 1), executable='~\\.pyenv\\pyenv-win\\versions\\3.13.0rc1\\python.exe', architecture='64bit', implementation='cpython', metadata={}, shadowed=False)```
```

### Python.org search ###

Python.org searches are handled by the `ducktools.pythonfinder.pythonorg_search` module.

```python
from packaging.specifiers import SpecifierSet
from ducktools.pythonfinder.pythonorg_search import PythonOrgSearch

# If system and machine are not provided this uses platform.system() and platform.machine()
searcher = PythonOrgSearch(system="Windows", machine="AMD64")

all_releases = searcher.releases
all_release_files = searcher.release_files
all_312_releases = searcher.matching_versions(SpecifierSet("~=3.12.0"))
all_312_downloads = searcher.matching_versions(SpecifierSet("~=3.12.0"))
all_312_311_win_binaries = searcher.all_matching_binaries(SpecifierSet(">=3.11.0, <3.13"))
latest_312_311_win_binaries = searcher.latest_minor_binaries(SpecifierSet(">=3.11.0, <3.13"))
latest_matching_win_binary = searcher.latest_binary_match(SpecifierSet(">=3.10"))
latest_prerelease_binary = searcher.latest_binary_match(SpecifierSet(">=3.10"), prereleases=True)
```

## Why? ##

For the purposes of PEP723 script dependencies and other releated tools
it may be useful to find another version of python other than the one currently running 
in order to satisfy the `requires-python` field. 
This tool is intended to search for potential python installs to attempt to
satisfy such a requirement.

## Isn't there already a 'pythonfinder' module? ##

That module appears to require searching for a specific version and will find venv pythons.

In contrast `ducktools.pythonfinder` simply yields python installs as they are discovered
and will attempt to avoid returning virtualenv python installs
