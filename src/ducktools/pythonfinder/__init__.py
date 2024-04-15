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

# Find platform python versions

__version__ = "v0.1.1"

__all__ = [
    "get_python_installs",
    "list_python_installs",
    "PythonInstall",
]

import sys
from .shared import PythonInstall

match sys.platform:  # pragma: no cover
    case "win32":
        from .win32 import get_python_installs
    case "darwin":
        from .darwin import get_python_installs
    case _:
        from .linux import get_python_installs


def list_python_installs():
    return sorted(get_python_installs(), reverse=True, key=lambda x: x.version)
