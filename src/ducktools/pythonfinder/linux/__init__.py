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

from ..shared import PythonInstall, get_folder_pythons, get_uv_pythons, get_uv_python_path
from .pyenv_search import get_pyenv_pythons


def get_path_pythons() -> Iterator[PythonInstall]:
    exe_names = set()

    path_folders = os.environ.get("PATH", "").split(":")
    pyenv_root = os.environ.get("PYENV_ROOT")
    uv_root = get_uv_python_path()

    excluded_folders = [pyenv_root, uv_root]

    for fld in path_folders:
        # Don't retrieve pyenv installs
        skip_folder = False
        for exclude in excluded_folders:
            if exclude and fld.startswith(exclude):
                skip_folder = True
                break

        if skip_folder:
            continue

        if not os.path.exists(fld):
            continue

        for install in get_folder_pythons(fld):
            name = os.path.basename(install.executable)
            if name in exe_names:
                install.shadowed = True
            else:
                exe_names.add(name)
            yield install


def get_python_installs(*, query_executables=True):
    listed_pythons = set()

    chain_commands = [
        get_pyenv_pythons(query_executables=query_executables),
        get_uv_pythons(query_executables=query_executables),
    ]
    if query_executables:
        chain_commands.append(get_path_pythons())

    for py in itertools.chain.from_iterable(chain_commands):
        if py.executable not in listed_pythons:
            yield py
            listed_pythons.add(py.executable)
