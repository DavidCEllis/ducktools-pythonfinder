# ducktools-pythonfinder
# Copyright (C) 2024 David C Ellis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import os.path
import itertools
from _collections_abc import Iterator

from ..shared import PythonInstall, get_folder_pythons
from .pyenv_search import get_pyenv_pythons


PATH_FOLDERS = os.environ.get("PATH").split(":")
_PYENV_ROOT = os.environ.get("PYENV_ROOT")


def get_path_pythons() -> Iterator[PythonInstall]:
    exe_names = set()

    for fld in PATH_FOLDERS:
        # Don't retrieve pyenv installs
        if _PYENV_ROOT and fld.startswith(_PYENV_ROOT):
            continue
        elif not os.path.exists(fld):
            continue

        for install in get_folder_pythons(fld):
            name = os.path.basename(install.executable)
            if name not in exe_names:
                yield install
                exe_names.add(name)


def get_python_installs():
    listed_pythons = set()

    for py in itertools.chain(get_pyenv_pythons(), get_path_pythons()):
        if py.executable not in listed_pythons:
            yield py
            listed_pythons.add(py.executable)
