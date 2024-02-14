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

from ..shared import PythonInstall


PYENV_VERSIONS_FOLDER = os.path.join(os.environ.get("PYENV_ROOT", ""), "versions")


def get_pyenv_pythons(
    versions_folder: str | os.PathLike = PYENV_VERSIONS_FOLDER,
) -> Iterator[PythonInstall]:
    if not os.path.exists(versions_folder):
        return

    for p in os.scandir(versions_folder):
        executable = os.path.join(p.path, "python.exe")

        if os.path.exists(executable):
            match p.name.split("-"):
                case (version, arch):
                    # win32 in pyenv name means 32 bit python install
                    # 'arm' is the only alternative which will be 64bit
                    arch = "32bit" if arch == "win32" else "64bit"
                    try:
                        yield PythonInstall.from_str(
                            version, executable, architecture=arch
                        )
                    except ValueError:
                        pass
                case (version,):
                    # If no arch given pyenv will be 64 bit
                    try:
                        yield PythonInstall.from_str(
                            version, executable, architecture="64bit"
                        )
                    except ValueError:
                        pass
                case _:
                    pass  # Skip unrecognised versions
