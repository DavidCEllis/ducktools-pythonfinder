# ducktools-pythonfinder
# MIT License
#
# Copyright (c) 2023-2024 David C Ellis
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
            split_version = p.name.split("-")

            # If there are 1 or 2 arguments this is a recognised version
            # Otherwise it is unrecognised
            if len(split_version) == 2:
                version, arch = split_version

                # win32 in pyenv name means 32 bit python install
                # 'arm' is the only alternative which will be 64bit
                arch = "32bit" if arch == "win32" else "64bit"
                try:
                    yield PythonInstall.from_str(
                        version, executable, architecture=arch
                    )
                except ValueError:
                    pass
            elif len(split_version) == 1:
                version = split_version[0]
                try:
                    yield PythonInstall.from_str(
                        version, executable, architecture="64bit"
                    )
                except ValueError:
                    pass

