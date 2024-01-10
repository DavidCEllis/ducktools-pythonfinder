from ..linux.pyenv_search import get_pyenv_pythons


def get_python_installs():
    return sorted(get_pyenv_pythons(), key=lambda x: x.version, reverse=True)
