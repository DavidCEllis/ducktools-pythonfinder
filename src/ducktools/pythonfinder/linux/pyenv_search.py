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

"""
Discover python installs that have been created with pyenv
"""

import os
import os.path
from _collections_abc import Iterator

from ducktools.lazyimporter import LazyImporter, ModuleImport

from ..shared import PythonInstall
from .. import details_script

_laz = LazyImporter(
    [
        ModuleImport("re"),
        ModuleImport("subprocess"),
        ModuleImport("json"),
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
                details_output = _laz.subprocess.run(
                    [executable, details_script.__file__],
                    capture_output=True,
                    text=True,
                ).stdout

                if details_output:
                    try:
                        details = _laz.json.loads(details_output)
                    except _laz.json.JSONDecodeError:
                        pass
                    else:
                        yield PythonInstall.from_json(**details)
