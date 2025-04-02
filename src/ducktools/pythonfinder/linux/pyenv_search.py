# ducktools-pythonfinder
# MIT License
#
# Copyright (c) 2023-2025 David C Ellis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

"""
Discover python installs that have been created with pyenv
"""

import os
import os.path
from _collections_abc import Iterator

from ducktools.lazyimporter import LazyImporter, FromImport, ModuleImport

from ..shared import PythonInstall, DetailFinder, INSTALLER_CACHE_PATH

_laz = LazyImporter(
    [
        ModuleImport("json"),
        ModuleImport("re"),
        FromImport("subprocess", "run"),
    ]
)


def get_pyenv_root() -> str | None:
    # Check if the environment variable exists, if so use that
    # As a backup try to run pyenv to obtain the root folder
    pyenv_root = os.environ.get("PYENV_ROOT")
    if not pyenv_root:
        try:
            with open(INSTALLER_CACHE_PATH) as f:
                installer_cache = _laz.json.load(f)
        except (FileNotFoundError, _laz.json.JSONDecodeError):
            installer_cache = {}

        pyenv_root = installer_cache.get("pyenv")
        if pyenv_root is None or not os.path.exists(pyenv_root):
            try:
                output = _laz.run(["pyenv", "root"], capture_output=True, text=True)
            except FileNotFoundError:
                return None

            pyenv_root = output.stdout.strip()

            installer_cache["pyenv"] = pyenv_root
            os.makedirs(os.path.dirname(INSTALLER_CACHE_PATH), exist_ok=True)
            with open(INSTALLER_CACHE_PATH, 'w') as f:
                _laz.json.dump(installer_cache, f)

    return pyenv_root


def get_pyenv_pythons(
    versions_folder: str | os.PathLike | None = None,
    *,
    finder: DetailFinder = None,
) -> Iterator[PythonInstall]:
    if versions_folder is None:
        if pyenv_root := get_pyenv_root():
            versions_folder = os.path.join(pyenv_root, "versions")

    if versions_folder is None or not os.path.exists(versions_folder):
        return

    # Sorting puts standard python versions before alternate implementations
    # This can lead to much faster returns by potentially yielding
    # the required python version before checking pypy/graalpy/micropython

    finder = DetailFinder() if finder is None else finder

    with finder:
        for p in sorted(os.scandir(versions_folder), key=lambda x: x.path):
            # Don't include folders that are venvs
            venv_indicator = os.path.join(p.path, "pyvenv.cfg")
            if os.path.exists(venv_indicator):
                continue

            executable = os.path.join(p.path, "bin/python")
            if os.path.exists(executable):
                install = finder.get_install_details(executable, managed_by="pyenv")
                if install:
                    yield install
