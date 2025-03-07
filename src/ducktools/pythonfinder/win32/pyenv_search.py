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

import os
import os.path
from _collections_abc import Iterator

from ..shared import PythonInstall, DetailFinder


def get_pyenv_root() -> str | None:
    # Check if the environment variable exists, if so use that
    # Windows PYENV does not have the `pyenv root` command to use as a backup.
    pyenv_root = os.environ.get("PYENV_ROOT")
    return pyenv_root


def get_pyenv_pythons(
    versions_folder: str | os.PathLike | None = None,
    *,
    query_executables: bool = True,
    finder: DetailFinder | None = None,
) -> Iterator[PythonInstall]:

    if versions_folder is None:
        if pyenv_root := get_pyenv_root():
            versions_folder = os.path.join(pyenv_root, "versions")

    if versions_folder is None or not os.path.exists(versions_folder):
        return

    finder = DetailFinder() if finder is None else finder

    with finder:
        for p in os.scandir(versions_folder):
            path_base = os.path.basename(p.path)

            if query_executables:
                # Check for pypy/graalpy
                if path_base.startswith("pypy"):
                    executable = os.path.join(p.path, "pypy.exe")
                    if os.path.exists(executable):
                        yield finder.get_install_details(executable, managed_by="pyenv")
                        continue
                elif path_base.startswith("graalpy"):
                    # Graalpy exe in bin subfolder
                    executable = os.path.join(p.path, "bin", "graalpy.exe")
                    if os.path.exists(executable):
                        yield finder.get_install_details(executable, managed_by="pyenv")
                        continue

            # Regular CPython
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
                            version=version,
                            executable=executable,
                            architecture=arch,
                            managed_by="pyenv",
                        )
                    except ValueError:
                        pass
                elif len(split_version) == 1:
                    version = split_version[0]
                    try:
                        yield PythonInstall.from_str(
                            version=version,
                            executable=executable,
                            architecture="64bit",
                            managed_by="pyenv",
                        )
                    except ValueError:
                        pass
