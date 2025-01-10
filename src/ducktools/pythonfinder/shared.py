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

from _collections_abc import Iterator

from ducktools.classbuilder.prefab import Prefab, attribute
from ducktools.lazyimporter import LazyImporter, ModuleImport, FromImport

from . import details_script

_laz = LazyImporter(
    [
        FromImport("glob", "glob"),
        ModuleImport("json"),
        ModuleImport("platform"),
        ModuleImport("re"),
        ModuleImport("subprocess"),
        ModuleImport("tempfile"),
        ModuleImport("zipfile"),
    ]
)


FULL_PY_VER_RE = r"(?P<major>\d+)\.(?P<minor>\d+)\.?(?P<micro>\d*)-?(?P<releaselevel>a|b|c|rc)?(?P<serial>\d*)?"

UV_PYTHON_RE = (
    r"(?P<implementation>[a-zA-Z]+)"
    r"-(?P<version>\d+\.\d+\.\d*[a-zA-Z]*\d*)\+?(?P<extra>.*?)?"
    r"-(?P<platform>\w*)"
    r"-(?P<arch>\w*)"
    r"-.*"
)


def version_str_to_tuple(version):
    parsed_version = _laz.re.fullmatch(FULL_PY_VER_RE, version)

    if not parsed_version:
        raise ValueError(f"{version!r} is not a recognised Python version string.")

    major, minor, micro, releaselevel, serial = parsed_version.groups()

    if releaselevel in {"a", "dev"}:
        releaselevel = "alpha"
    elif releaselevel == "b":
        releaselevel = "beta"
    elif releaselevel in {"c", "rc"}:
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

    if serial == 0 or not releaselevel:
        serial = ""
    else:
        serial = f"{serial}"

    return f"{major}.{minor}.{micro}{releaselevel}{serial}"


class DetailsScript(Prefab):
    """
    Class to obtain and cache the source code of details_script.py
    to use on external Pythons.
    """
    _source_code: str | None = attribute(default=None, private=True)

    def get_source_code(self):
        if self._source_code is None:
            if os.path.exists(details_file := details_script.__file__):
                with open(details_file) as f:
                    self._source_code = f.read()
            elif os.path.splitext(archive_path := sys.argv[0])[1].startswith(".pyz"):
                script_path = os.path.relpath(details_script.__file__, archive_path)
                if sys.platform == "win32":
                    # Windows paths have backslashes, these do not work in zipfiles
                    script_path = script_path.replace("\\", "/")
                script = _laz.zipfile.Path(archive_path, script_path)
                self._source_code = script.read_text()
            else:
                raise FileNotFoundError(f"Could not find {details_script.__file__!r}")

        return self._source_code


details = DetailsScript()


class PythonInstall(Prefab):
    version: tuple[int, int, int, str, int]
    executable: str
    architecture: str = "64bit"
    implementation: str = "cpython"
    managed_by: str | None = None
    metadata: dict = attribute(default_factory=dict)
    shadowed: bool = False
    _implementation_version: tuple[int, int, int, str, int] | None = attribute(default=None, private=True)

    def __prefab_post_init__(
        self,
        version: tuple[int, int, int] | tuple[int, int, int, str, int]
    ):
        if len(version) == 3:
            # Micropython gives an invalid 3 part version here
            # Add the extras to avoid breaking
            self.version = tuple([*version, "final", 0])  # type: ignore
        else:
            self.version = version

    @property
    def version_str(self) -> str:
        return version_tuple_to_str(self.version)

    @property
    def implementation_version(self) -> tuple[int, int, int, str, int] | None:
        if self._implementation_version is None:
            if implementation_ver := self.metadata.get(f"{self.implementation}_version"):
                if len(implementation_ver) == 3:
                    self._implementation_version = tuple([*implementation_ver, "final", 0])  # type: ignore
                else:
                    self._implementation_version = implementation_ver
            else:
                self._implementation_version = self.version

        return self._implementation_version

    @property
    def implementation_version_str(self) -> str:
        return version_tuple_to_str(self.implementation_version)

    @classmethod
    def from_str(
        cls,
        version: str,
        executable: str,
        architecture: str = "64bit",
        implementation: str = "cpython",
        managed_by: str | None = None,
        metadata: dict | None = None,
    ):
        version_tuple = version_str_to_tuple(version)

        # noinspection PyArgumentList
        return cls(
            version=version_tuple,
            executable=executable,
            architecture=architecture,
            implementation=implementation,
            managed_by=managed_by,
            metadata=metadata,
        )

    @classmethod
    def from_json(cls, version, executable, architecture, implementation, metadata, managed_by=None):
        if arch_ver := metadata.get(f"{implementation}_version"):
            metadata[f"{implementation}_version"] = tuple(arch_ver)

        # noinspection PyArgumentList
        return cls(
            version=tuple(version),
            executable=executable,
            architecture=architecture,
            implementation=implementation,
            managed_by=managed_by,
            metadata=metadata,
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


def get_install_details(executable: str, managed_by=None) -> PythonInstall | None:
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
    except OSError:
        # Something else has gone wrong
        return None
    except (_laz.subprocess.CalledProcessError, FileNotFoundError):
        # Potentially this is micropython which does not support
        # piping from stdin. Try using a file in a temporary folder.
        # Python 3.12 has delete_on_close that would make TemporaryFile
        # Usable on windows but for now use a directory
        with _laz.tempfile.TemporaryDirectory() as tempdir:
            temp_script = os.path.join(tempdir, "details_script.py")
            with open(temp_script, "w") as f:
                f.write(source)
            try:
                detail_output = _laz.subprocess.run(
                    [executable, temp_script],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
            except (_laz.subprocess.CalledProcessError, FileNotFoundError):
                return None

    try:
        output = _laz.json.loads(detail_output)
    except _laz.json.JSONDecodeError as e:
        return None

    return PythonInstall.from_json(**output, managed_by=managed_by)


def get_folder_pythons(
    base_folder: str | os.PathLike,
    basenames: tuple[str] = ("python", "pypy")
):
    regexes = [_python_exe_regex(name) for name in basenames]

    with os.scandir(base_folder) as fld:
        for file_path in fld:
            try:
                is_file = file_path.is_file()
            except PermissionError:
                continue
            
            if (
                is_file
                and any(reg.fullmatch(file_path.name) for reg in regexes)
            ):
                p = file_path.path
                if file_path.is_symlink():
                    # Might be a venv - look for pyvenv.cfg in parent
                    fld = os.path.dirname(p)
                    if os.path.exists(os.path.join(fld, "../pyvenv.cfg")):
                        continue
                else:
                    p = file_path.path
                install = get_install_details(p)
                if install:
                    yield install


# UV Specific finder
def get_uv_python_path() -> str | None:
    try:
        uv_python_find = _laz.subprocess.run(
            ["uv", "python", "dir"],
            check=True,
            text=True,
            capture_output=True
        )
    except (_laz.subprocess.CalledProcessError, FileNotFoundError):
        uv_python_dir = None
    else:
        # remove newline
        uv_python_dir = uv_python_find.stdout.strip()

    return uv_python_dir


def _implementation_from_uv_dir(
    direntry: os.DirEntry,
    query_executables: bool = True,
) -> PythonInstall | None:
    python_exe = "python.exe" if sys.platform == "win32" else "bin/python"
    python_path = os.path.join(direntry, python_exe)

    install: PythonInstall | None = None

    if os.path.exists(python_path):
        if match := _laz.re.fullmatch(UV_PYTHON_RE, direntry.name):
            implementation, version, extra, platform, arch = match.groups()
            metadata = {
                "freethreaded": "freethreaded" in extra,
            }

            try:
                if implementation in {"cpython"}:
                    install = PythonInstall.from_str(
                        version=version,
                        executable=python_path,
                        architecture="32bit" if arch in {"i686", "armv7"} else "64bit",
                        implementation=implementation,
                        metadata=metadata,
                        managed_by="Astral UV",
                    )
            except ValueError:
                pass

        if install is None:
            # Directory name format has changed or this is an alternate implementation
            # Slow backup - ask python itself
            if query_executables:
                install = get_install_details(python_path)
                install.managed_by = "Astral UV"

    return install


def get_uv_pythons(query_executables=True) -> Iterator[PythonInstall]:
    # This takes some shortcuts over the regular pythonfinder
    # As the UV folders give the python version and the implementation
    if uv_python_path := get_uv_python_path():
        if os.path.exists(uv_python_path):
            with os.scandir(uv_python_path) as fld:
                for f in fld:
                    if (
                        f.is_dir()
                        and (install := _implementation_from_uv_dir(f, query_executables))
                    ):
                        yield install
