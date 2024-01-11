from ..linux import get_pyenv_pythons, get_dist_pythons


def get_python_installs():
    return sorted(
        get_pyenv_pythons() + get_dist_pythons(),
        key=lambda x: x.version,
        reverse=True,
    )
