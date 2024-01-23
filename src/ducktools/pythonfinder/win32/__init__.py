from .pyenv_search import get_pyenv_pythons
from .registry_search import get_registered_pythons


def get_python_installs():
    registered_pythons = get_registered_pythons()
    pyenv_pythons = get_pyenv_pythons()

    # Pyenv pythons should only be listed if they are not already included
    registered_exes = {p.executable for p in registered_pythons}
    pythons = registered_pythons + [
        p for p in pyenv_pythons if p.executable not in registered_exes
    ]

    return sorted(
        pythons,
        key=lambda x: x.version,
        reverse=True,
    )
