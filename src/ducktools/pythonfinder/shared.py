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

import sys
import os
import os.path

from ducktools.classbuilder import slotclass, Field, SlotFields
from ducktools.lazyimporter import LazyImporter, ModuleImport, FromImport

from . import details_script

_laz = LazyImporter(
    [
        ModuleImport("re"),
        ModuleImport("subprocess"),
        ModuleImport("platform"),
        FromImport("glob", "glob"),
        ModuleImport("json"),
        ModuleImport("zipfile"),
    ]
)


FULL_PY_VER_RE = r"(?P<major>\d+)\.(?P<minor>\d+)\.?(?P<micro>\d*)(?P<releaselevel>[a-zA-Z]*)(?P<serial>\d*)"


def version_str_to_tuple(version):
    parsed_version = _laz.re.fullmatch(FULL_PY_VER_RE, version)

    if not parsed_version:
        raise ValueError(f"{version!r} is not a recognised Python version string.")

    major, minor, micro, releaselevel, serial = parsed_version.groups()

    if releaselevel == "a":
        releaselevel = "alpha"
    elif releaselevel == "b":
        releaselevel = "beta"
    elif releaselevel == "rc":
        releaselevel = "candidate"
    else:
        releaselevel = "final"

    version_tuple = (
        int(major),
        int(minor),
        int(micro) if micro else 0,
        releaselevel,
        int(serial if serial != "" else 0),
    )
    return version_tuple


def version_tuple_to_str(version_tuple):
    major, minor, micro, releaselevel, serial = version_tuple

    if releaselevel == "alpha":
        releaselevel = "a"
    elif releaselevel == "beta":
        releaselevel = "b"
    elif releaselevel == "candidate":
        releaselevel = "rc"
    else:
        releaselevel = ""

    if serial == 0:
        serial = ""
    else:
        serial = f"{serial}"

    return f"{major}.{minor}.{micro}{releaselevel}{serial}"


@slotclass
class DetailsScript:
    """
    Class to obtain and cache the source code of details_script.py
    to use on external Pythons.
    """
    __slots__ = SlotFields(
        _source_code=Field(default=None)
    )

    _source_code: str | None

    def get_source_code(self):
        if self._source_code is None:
            if os.path.exists(details_file := details_script.__file__):
                with open(details_file) as f:
                    self._source_code = f.read()
            elif os.path.splitext(archive_path := sys.argv[0])[1].startswith(".pyz"):
                script_path = os.path.relpath(details_script.__file__, archive_path)
                script = _laz.zipfile.Path(archive_path, script_path)
                self._source_code = script.read_text()
            else:
                raise FileNotFoundError(f"Could not find {details_script.__file__!r}")

        return self._source_code


details = DetailsScript()


@slotclass
class PythonInstall:
    __slots__ = SlotFields(
        version=Field(),
        executable=Field(),
        architecture="64bit",
        implementation="cpython",
        metadata=Field(default_factory=dict),
        shadowed=False,
    )
    version: tuple[int, int, int, str, int]
    executable: str
    architecture: str
    implementation: str
    metadata: dict
    shadowed: bool

    @property
    def version_str(self) -> str:
        return version_tuple_to_str(self.version)

    @classmethod
    def from_str(
        cls,
        version: str,
        executable: str,
        architecture: str = "64bit",
        implementation: str = "cpython",
        metadata: dict | None = None,
    ):
        version_tuple = version_str_to_tuple(version)

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
        """
        Get the version of pip installed on a python install.

        :return: None if pip is not found or the command fails
                 version number as string otherwise.
        """
        pip_call = _laz.subprocess.run(
            [self.executable, "-c", "import pip; print(pip.__version__, end='')"],
            text=True,
            capture_output=True,
        )

        # Pip call failed
        if pip_call.returncode != 0:
            return None

        return pip_call.stdout


def _python_exe_regex(basename: str = "python"):
    if sys.platform == "win32":
        return _laz.re.compile(rf"{basename}\d?\.?\d*\.exe")
    else:
        return _laz.re.compile(rf"{basename}\d?\.?\d*")


def get_install_details(executable: str) -> PythonInstall | None:
    try:
        source = details.get_source_code()
    except FileNotFoundError:
        return None

    try:
        detail_output = _laz.subprocess.run(
            [executable, "-"],
            input=source,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (_laz.subprocess.CalledProcessError, FileNotFoundError):
        return None

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
