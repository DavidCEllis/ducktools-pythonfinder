from _collections_abc import Iterator

from ..shared import PythonInstall
from .pyenv_search import get_pyenv_pythons
from .registry_search import get_registered_pythons


def get_python_installs() -> Iterator[PythonInstall]:
    yield from get_registered_pythons()
    yield from get_pyenv_pythons()
