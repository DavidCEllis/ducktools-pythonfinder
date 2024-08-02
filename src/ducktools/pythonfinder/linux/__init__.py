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
            if name in exe_names:
                install.shadowed = True
            else:
                exe_names.add(name)
            yield install


def get_python_installs():
    listed_pythons = set()

    for py in itertools.chain(get_pyenv_pythons(), get_path_pythons()):
        if py.executable not in listed_pythons:
            yield py
            listed_pythons.add(py.executable)
