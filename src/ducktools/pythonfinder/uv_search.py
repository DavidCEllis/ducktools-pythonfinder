import os
import os.path
import sys

try:
    from _collections_abc import Iterator
except ImportError:
    from collections.abc import Iterator

from ducktools.lazyimporter import LazyImporter, ModuleImport

from .shared import (
    INSTALLER_CACHE_PATH,
    DetailFinder,
    PythonInstall,
)

_laz = LazyImporter(
    [
        ModuleImport("json"),
        ModuleImport("subprocess"),
    ]
)

# UV Specific finder
def get_uv_python_path() -> str | None:
    # Attempt to get cache
    try:
        with open(INSTALLER_CACHE_PATH) as f:
            installer_cache = _laz.json.load(f)
    except (FileNotFoundError, _laz.json.JSONDecodeError):
        installer_cache = {}

    uv_python_dir = installer_cache.get("uv")
    if uv_python_dir and os.path.exists(uv_python_dir):
        return uv_python_dir

    # Cache failed
    try:
        uv_python_find = _laz.subprocess.run(
            ["uv", "python", "dir"],
            check=True,
            text=True,
            capture_output=True
        )
    except (_laz.subprocess.CalledProcessError, FileNotFoundError):
        uv_python_dir = None
    else:
        # remove newline
        uv_python_dir = uv_python_find.stdout.strip()

    # Fill cache and update the cache file
    installer_cache["uv"] = uv_python_dir
    os.makedirs(os.path.dirname(INSTALLER_CACHE_PATH), exist_ok=True)
    with open(INSTALLER_CACHE_PATH, 'w') as f:
        _laz.json.dump(installer_cache, f)

    return uv_python_dir


def _implementation_from_uv_dir(
    direntry: os.DirEntry,
    finder: DetailFinder | None = None,
) -> PythonInstall | None:
    if sys.platform == "win32":
        python_paths = [
            os.path.join(direntry, "python.exe"),
            os.path.join(direntry, "bin/python.exe"),  # graalpy
        ]
    else:
        python_paths = [
            os.path.join(direntry, "bin/python")
        ]

    install: PythonInstall | None = None
    finder = DetailFinder() if finder is None else finder

    for pth in python_paths:
        if os.path.exists(pth):
            install = finder.get_install_details(pth, managed_by="Astral")
            break

    return install


def get_uv_pythons(finder=None) -> Iterator[PythonInstall]:
    """
    Search UVs python folders for unique python installs.

    If multiple folders are found with the same Python version,
    implementation name and implementation version and freethreading support
    then only the executable with the shortest path will be given.

    So if you have CPython 3.x.y installed in 3.x.y and 3.x directories
    only the install with the 3.x path will be given. This is the
    case even if the 3.x path is a symlink to the 3.x.y folder.
    """
    # Filtering is done by the triple of
    # (python version, implementation name, implementation version)
    if (
        (uv_python_path := get_uv_python_path())
        and os.path.exists(uv_python_path)
    ):
        finder = DetailFinder() if finder is None else finder

        with finder, os.scandir(uv_python_path) as fld:
            unique_releases: dict[tuple[str, str, str, bool], list[PythonInstall]] = {}

            # Create a folder of stdlib paths to folders
            for f in fld:
                if (
                    f.is_dir()
                    and (install := _implementation_from_uv_dir(f, finder=finder))
                ):
                    identifier = (
                        install.version_str,
                        install.implementation,
                        install.implementation_version_str,
                        install.metadata.get("freethreaded", False),
                    )
                    release_group = unique_releases.setdefault(identifier, [])
                    release_group.append(install)

            for install_group in unique_releases.values():
                # Sort the group by path length so the shortest item is first
                install_group.sort(key=lambda py: len(py.executable))
                yield install_group[0]
