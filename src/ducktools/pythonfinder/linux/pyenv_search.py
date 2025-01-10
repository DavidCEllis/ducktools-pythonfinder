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


"""
Discover python installs that have been created with pyenv
"""

import os
import os.path
from _collections_abc import Iterator

from ducktools.lazyimporter import LazyImporter, ModuleImport

from ..shared import PythonInstall, get_install_details, FULL_PY_VER_RE, version_str_to_tuple

_laz = LazyImporter(
    [
        ModuleImport("re"),
    ]
)

# pyenv folder name for pypy
PYPY_VER_RE = r"^pypy(?P<pyversion>\d{1,2}\.\d+)-(?P<pypyversion>[\d\.]*)$"

PYENV_VERSIONS_FOLDER = os.path.join(os.environ.get("PYENV_ROOT", ""), "versions")


def get_pyenv_pythons(
    versions_folder: str | os.PathLike = PYENV_VERSIONS_FOLDER,
    *,
    query_executables: bool = True,
) -> Iterator[PythonInstall]:
    if not os.path.exists(versions_folder):
        return

    # Sorting puts standard python versions before alternate implementations
    # This can lead to much faster returns by potentially yielding
    # the required python version before checking pypy/graalpy/micropython

    for p in sorted(os.scandir(versions_folder), key=lambda x: x.path):
        executable = os.path.join(p.path, "bin/python")

        if os.path.exists(executable):
            if p.name.endswith("t"):
                freethreaded = True
                version = p.name[:-1]
            else:
                freethreaded = False
                version = p.name
            if _laz.re.fullmatch(FULL_PY_VER_RE, version):
                version_tuple = version_str_to_tuple(version)
                metadata = {}
                if version_tuple >= (3, 13):
                    metadata["freethreaded"] = freethreaded
                yield PythonInstall(
                    version=version_tuple,
                    executable=executable,
                    metadata=metadata,
                    managed_by="pyenv",
                )
            elif query_executables and (install := get_install_details(executable, managed_by="pyenv")):
                yield install
