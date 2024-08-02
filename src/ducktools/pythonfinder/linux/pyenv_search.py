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

from ..shared import PythonInstall, get_install_details

_laz = LazyImporter(
    [
        ModuleImport("re"),
    ]
)

# pyenv folder names
PYTHON_VER_RE = r"\d{1,2}\.\d{1,2}\.\d+[a-z]*\d*"
PYPY_VER_RE = r"^pypy(?P<pyversion>\d{1,2}\.\d+)-(?P<pypyversion>[\d\.]*)$"

# 'pypy -V' output matcher
PYPY_V_OUTPUT = (
    r"(?is)python (?P<python_version>\d+\.\d+\.\d+[a-z]*\d*).*?"
    r"pypy (?P<pypy_version>\d+\.\d+\.\d+[a-z]*\d*).*"
)

PYENV_VERSIONS_FOLDER = os.path.join(os.environ.get("PYENV_ROOT", ""), "versions")


def get_pyenv_pythons(
    versions_folder: str | os.PathLike = PYENV_VERSIONS_FOLDER,
) -> Iterator[PythonInstall]:
    if not os.path.exists(versions_folder):
        return

    # Sorting puts standard python versions before pypy
    # This can lead to much faster returns by potentially yielding
    # the required python version before checking pypy

    for p in sorted(os.scandir(versions_folder), key=lambda x: x.path):
        executable = os.path.join(p.path, "bin/python")

        if os.path.exists(executable):
            if _laz.re.fullmatch(PYTHON_VER_RE, p.name):
                yield PythonInstall.from_str(p.name, executable)
            elif _laz.re.fullmatch(PYPY_VER_RE, p.name):
                if install := get_install_details(executable):
                    yield install
