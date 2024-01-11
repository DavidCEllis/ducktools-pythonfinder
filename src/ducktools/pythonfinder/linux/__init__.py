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
