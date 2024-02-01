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
        if arch_ver := metadata.get(f"{implementation}_version"):
            metadata[f"{implementation}_version"] = tuple(arch_ver)

        return cls(
            tuple(version), executable, architecture, implementation, metadata  # noqa
        )

    def get_pip_version(self) -> str | None:
        pip_call = _laz.subprocess.run(
            [
                self.executable,
                "-c",
                "import pip; print(pip.__version__, end='')"
            ],
            text=True,
            capture_output=True,
        )

        # Pip call failed
        if pip_call.return_code != 0:
            return None

        return pip_call.stdout


def _python_exe_regex(basename: str = "python"):
    if sys.platform == "win32":
        return _laz.re.compile(rf"{basename}\d?\.?\d*\.exe")
    else:
        return _laz.re.compile(rf"{basename}\d?\.?\d*")


def get_install_details(executable: str) -> PythonInstall | None:
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
    except _laz.json.JSONDecodeError:
        return None

    return PythonInstall.from_json(**output)


def get_folder_pythons(
    base_folder: str | os.PathLike, basenames: tuple[str] = ("python", "pypy")
):
    regexes = [_python_exe_regex(name) for name in basenames]

    with os.scandir(base_folder) as fld:
        for file_path in fld:
            if (
                not file_path.is_symlink()
                and file_path.is_file()
                and any(reg.fullmatch(file_path.name) for reg in regexes)
            ):
                install = get_install_details(file_path.path)
                if install:
                    yield install
