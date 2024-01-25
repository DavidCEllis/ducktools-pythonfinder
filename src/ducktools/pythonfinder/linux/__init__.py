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
from _collections_abc import Iterator

from ..shared import PythonInstall, get_folder_pythons
from .pyenv_search import get_pyenv_pythons


PATH_FOLDERS = os.environ.get("PATH").split(":")


def get_path_pythons() -> Iterator[PythonInstall]:
    exe_names = set()

    for fld in PATH_FOLDERS:
        if "/.pyenv" in fld:
            continue

        for install in get_folder_pythons(fld):
            name = os.path.basename(install.executable)
            if name not in exe_names:
                yield install


def get_python_installs():
    yield from get_pyenv_pythons()
    yield from get_path_pythons()
