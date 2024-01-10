from .pyenv_search import get_pyenv_pythons
from .registry_search import get_registered_pythons


def get_python_installs():
    return sorted(
        get_pyenv_pythons() + get_registered_pythons(),
        key=lambda x: x.version,
        reverse=True,
    )
