# DuckTools-EnvMan
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

import sys
import os
import os.path

from prefab_classes import prefab, attribute
from ducktools.lazyimporter import LazyImporter, ModuleImport, FromImport

_laz = LazyImporter([
    ModuleImport("re"),
    ModuleImport("subprocess"),
    ModuleImport("platform"),
    FromImport("glob", "glob"),
])


@prefab
class PythonInstall:
    version: tuple[int, ...]
    executable: str
    architecture: str = "64bit"
    implementation: str = "cpython"
    metadata: dict = attribute(default_factory=dict)

    @classmethod
    def from_str(
        cls,
        version: str,
        executable: str,
        architecture: str = "64bit",
        implementation: str = "cpython",
        metadata: dict | None = None,
    ):
        version_tuple = tuple(int(val) for val in version.split("."))

        # noinspection PyArgumentList
        return cls(
            version=version_tuple,
            executable=executable,
            architecture=architecture,
            implementation=implementation,
            metadata=metadata,
        )


# Python finder for folders
class _LazyPythonRegexes:
    def __init__(self, basename="python", version_re=r"^Python\s+(\d+.\d+.\d+)$"):
        self.basename = basename
        self.version_re = version_re
        self._is_potential_python = None
        self._python_v_re = None

    @property
    def is_potential_python(self):
        # Python filenames - more specific than the glob to eliminate other packages
        if not self._is_potential_python:
            if sys.platform == "win32":
                self._is_potential_python = _laz.re.compile(rf"^{self.basename}\d?\.?\d*\.exe$")
            else:
                self._is_potential_python = _laz.re.compile(rf"^{self.basename}\d?\.?\d*$")
        return self._is_potential_python

    @property
    def python_v_re(self):
        # Python version from subprocess output
        if not self._python_v_re:
            self._python_v_re = _laz.re.compile(self.version_re)
        return self._python_v_re


REGEXES = _LazyPythonRegexes()


def get_folder_pythons(base_folder: str | os.PathLike):
    installs = []
    if sys.platform == "win32":
        potential_py = _laz.glob(os.path.join(base_folder, "python*.exe"))
    else:
        potential_py = _laz.glob(os.path.join(base_folder, "python*"))
    for executable_path in potential_py:
        basename = os.path.relpath(executable_path, base_folder)
        if _laz.re.fullmatch(REGEXES.is_potential_python, basename):
            version_output = (
                _laz.subprocess.run([executable_path, "-V"], capture_output=True)
                .stdout.decode("utf-8")
                .strip()
            )

            version_match = _laz.re.match(REGEXES.python_v_re, version_output)
            if version_match:
                version_txt = version_match.group(1)
                installs.append(
                    PythonInstall.from_str(
                        version=version_txt,
                        executable=executable_path,
                        architecture=_laz.platform.architecture()[0],
                    )
                )

    return installs
