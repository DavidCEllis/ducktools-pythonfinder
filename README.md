# ducktools: pythonfinder #

Find python installs on Linux, Windows and MacOS.

Attempts to find python installed by `pyenv`, system python or python installs
correctly registered on Windows.

Usage:

```python
from ducktools.pythonfinder import get_python_installs

for install in get_python_installs():
    print(install)
```
