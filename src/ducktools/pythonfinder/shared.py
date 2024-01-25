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

from . import details_script

_laz = LazyImporter(
    [
        ModuleImport("re"),
        ModuleImport("subprocess"),
        ModuleImport("platform"),
        FromImport("glob", "glob"),
        ModuleImport("json"),
    ]
)


FULL_PY_VER_RE = r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<micro>\d+)(?P<releaselevel>[a-zA-Z]*)(?P<serial>\d*)"


@prefab
class PythonInstall:
    version: tuple[int, int, int, str, int]
    executable: str
    architecture: str = "64bit"
    implementation: str = "cpython"
    metadata: dict = attribute(default_factory=dict)

    @property
    def version_str(self) -> str:
        major, minor, micro, releaselevel, serial = self.version

        match releaselevel:
            case "alpha":
                releaselevel = "a"
            case "beta":
                releaselevel = "b"
            case "candidate":
                releaselevel = "rc"
            case _:
                releaselevel = ""

        if serial == 0:
            serial = ""
        else:
            serial = f"{serial}"

        return f"{major}.{minor}.{micro}{releaselevel}{serial}"

    @classmethod
    def from_str(
        cls,
        version: str,
        executable: str,
        architecture: str = "64bit",
        implementation: str = "cpython",
        metadata: dict | None = None,
    ):
        parsed_version = _laz.re.fullmatch(FULL_PY_VER_RE, version)

        if not parsed_version:
            raise ValueError(f"{version!r} is not a recognised Python version string.")

        major, minor, micro, releaselevel, serial = parsed_version.groups()

        match releaselevel:
            case "a":
                releaselevel = "alpha"
            case "b":
                releaselevel = "beta"
            case "rc":
                releaselevel = "candidate"
            case _:
                releaselevel = "final"

        version_tuple = (
            int(major),
            int(minor),
            int(micro),
            releaselevel,
            int(serial if serial != "" else 0),
        )

        # noinspection PyArgumentList
        return cls(
            version=version_tuple,
            executable=executable,
            architecture=architecture,
            implementation=implementation,
            metadata=metadata,
        )

    @classmethod
    def from_json(cls, version, executable, architecture, implementation, metadata):
        if arch_ver := metadata.get(f"{architecture}_version"):
            metadata[f"{architecture}_version"] = tuple(arch_ver)

        return cls(tuple(version), executable, architecture, implementation, metadata)  # noqa


def _python_exe_regex(basename: str = "python"):
    if sys.platform == "win32":
        return _laz.re.compile(rf"{basename}\d?\.?\d*\.exe")
    else:
        return _laz.re.compile(rf"{basename}\d?\.?\d*")


def parse_version_output(executable: str) -> PythonInstall | None:
    detail_output = (
        _laz.subprocess.run(
            [executable, details_script.__file__],
            capture_output=True,
        )
        .stdout.decode("utf-8")
        .strip()
    )

    try:
        output = _laz.json.loads(detail_output)
    except _laz.JSONDecodeError:
        return None

    return PythonInstall.from_json(**output)


def get_folder_pythons(base_folder: str | os.PathLike, basename="python"):
    installs = []
    if sys.platform == "win32":
        potential_py = _laz.glob(os.path.join(base_folder, f"{basename}*.exe"))
    else:
        potential_py = _laz.glob(os.path.join(base_folder, f"{basename}*"))

    py_exe_match = _python_exe_regex(basename)

    for executable_path in potential_py:
        basename = os.path.relpath(executable_path, base_folder)
        if _laz.re.fullmatch(py_exe_match, basename):
            install = parse_version_output(executable_path)

            if install:
                installs.append(install)

    return installs
