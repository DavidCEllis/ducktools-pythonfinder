from _collections_abc import Iterator
import itertools

from ..shared import PythonInstall
from .pyenv_search import get_pyenv_pythons
from .registry_search import get_registered_pythons


def get_python_installs() -> Iterator[PythonInstall]:
    listed_installs = set()
    for py in itertools.chain(get_registered_pythons(), get_pyenv_pythons()):
        if py.executable not in listed_installs:
            yield py
            listed_installs.add(py.executable)
