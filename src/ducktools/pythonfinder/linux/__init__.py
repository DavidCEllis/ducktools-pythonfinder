from ..shared import PythonInstall, get_folder_pythons
from .pyenv_search import get_pyenv_pythons


BIN_FOLDER = "/usr/bin"


def get_dist_pythons() -> list[PythonInstall]:
    return get_folder_pythons(BIN_FOLDER)


def get_python_installs():
    return sorted(
        get_pyenv_pythons() + get_dist_pythons(),
        key=lambda x: x.version,
        reverse=True,
    )
