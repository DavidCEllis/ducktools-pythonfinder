# ducktools-pythonfinder
# MIT License
#
# Copyright (c) 2023-2025 David C Ellis
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

from ducktools.classbuilder.prefab import Prefab, attribute, as_dict
from ducktools.lazyimporter import LazyImporter, ModuleImport, FromImport

from . import details_script

_laz = LazyImporter(
    [
        FromImport("glob", "glob"),
        ModuleImport("json"),
        ModuleImport("platform"),
        ModuleImport("re"),
        ModuleImport("shutil"),
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

# Cache for runtime details
# Code to work out where to store data
# Store in LOCALAPPDATA for windows, User folder for other operating systems
if sys.platform == "win32":
    # os.path.expandvars will actually import a whole bunch of other modules
    # Try just using the environment.
    if _local_app_folder := os.environ.get("LOCALAPPDATA"):
        if not os.path.isdir(_local_app_folder):
            raise FileNotFoundError(
                f"Could not find local app data folder {_local_app_folder}"
            )
    else:
        raise EnvironmentError(
            "Environment variable %LOCALAPPDATA% "
            "for local application data folder location "
            "not found"
        )
    USER_FOLDER = _local_app_folder
    CACHE_FOLDER = os.path.join(USER_FOLDER, "ducktools", "pythonfinder", "cache")
else:
    USER_FOLDER = os.path.expanduser("~")
    CACHE_FOLDER = os.path.join(USER_FOLDER, ".cache", "ducktools", "pythonfinder")


CACHE_VERSION = 1
DETAILS_CACHE_PATH = os.path.join(CACHE_FOLDER, f"runtime_cache_v{CACHE_VERSION}.json")
INSTALLER_CACHE_PATH = os.path.join(CACHE_FOLDER, "installer_details.json")


def purge_caches(cache_folder=CACHE_FOLDER):
    _laz.shutil.rmtree(cache_folder, ignore_errors=True)


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


class DetailFinder(Prefab):
    cache_path: str = DETAILS_CACHE_PATH
    details_script: DetailsScript = attribute(default_factory=DetailsScript)

    # Stores the dict loaded from the JSON file without processing
    _raw_cache: dict | None = attribute(default=None, private=True)

    # Indicates if the cache is known to have changed
    _dirty_cache: bool = attribute(default=False, private=True)

    # Increased each re-entry to the context manager
    # Decreased on exit
    # Save should only occur when all contexts exit
    _context_level: int = attribute(default=0, private=True)

    def __enter__(self):
        self._context_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context_level -= 1
        if (
            exc_type in {None, GeneratorExit}
            and self._dirty_cache
            and self._context_level == 0
        ):
            self.save()

    @property
    def raw_cache(self):
        if self._raw_cache is None:
            try:
                with open(self.cache_path) as f:
                    self._raw_cache = _laz.json.load(f)
            except (_laz.json.JSONDecodeError, FileNotFoundError):
                self._raw_cache = {}
        return self._raw_cache

    def save(self):
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, 'w') as f:
            _laz.json.dump(self.raw_cache, f, indent=4)

        self._dirty_cache = False

    def clear_invalid_runtimes(self):
        """
        Remove cache entries where the python.exe no longer exists
        """
        removed_runtimes: set[str] = set()
        for exe_path in self.raw_cache.copy().keys():
            if not os.path.exists(exe_path):
                self.raw_cache.pop(exe_path)
                removed_runtimes.add(exe_path)
        if removed_runtimes:
            self._dirty_cache = True

    def clear_cache(self):
        """
        Completely empty the cache
        """
        self._raw_cache = {}
        self._dirty_cache = True

    def query_install(
        self,
        exe_path: str,
        managed_by: str | None = None,
        metadata: dict | None = None,
    ) -> PythonInstall | None:
        """
        Query the details of a Python install directly

        :param exe_path: Path to the runtime .exe
        :param managed_by: Which tool manages this install (if any)
        :param metadata: Dictionary of install metadata
        :return: a PythonInstall if one exists at the exe Path
        """
        try:
            source = self.details_script.get_source_code()
        except FileNotFoundError:
            return None

        try:
            detail_output = _laz.subprocess.run(
                [exe_path, "-"],
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
                        [exe_path, temp_script],
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

        if metadata:
            output["metadata"].update(metadata)

        install = PythonInstall.from_json(**output, managed_by=managed_by)

        return install

    def get_install_details(
        self,
        exe_path: str,
        managed_by: str | None = None,
        metadata: dict | None = None,
    ) -> PythonInstall | None:
        exe_path = os.path.abspath(exe_path)
        mtime = os.stat(exe_path).st_mtime

        install = None
        if cached_details := self.raw_cache.get(exe_path):
            if cached_details["mtime"] == mtime:
                install = PythonInstall.from_json(**cached_details["install"])
            else:
                self.raw_cache.pop(exe_path)

        if install is None:
            install = self.query_install(exe_path, managed_by, metadata)
            if install:
                self.raw_cache[exe_path] = {
                    "mtime": mtime,
                    "install": as_dict(install)
                }
                self._dirty_cache = True

        return install


class PythonInstall(Prefab):
    version: tuple[int, int, int, str, int]
    executable: str
    architecture: str = "64bit"
    implementation: str = "cpython"
    managed_by: str | None = None
    metadata: dict = attribute(default_factory=dict)
    shadowed: bool = attribute(default=False, serialize=False)
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
    def from_json(
        cls,
        version,
        executable,
        architecture,
        implementation,
        metadata,
        managed_by=None,
    ):
        if arch_ver := metadata.get(f"{implementation}_version"):
            metadata[f"{implementation}_version"] = tuple(arch_ver)

        # noinspection PyArgumentList
        return cls(
            version=tuple(version),  # type: ignore
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


def get_folder_pythons(
    base_folder: str | os.PathLike,
    basenames: tuple[str] = ("python", "pypy"),
    finder: DetailFinder | None = None,
    managed_by: str | None = None,
):
    regexes = [_python_exe_regex(name) for name in basenames]

    finder = DetailFinder() if finder is None else finder

    with finder, os.scandir(base_folder) as fld:
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
                install = finder.get_install_details(p, managed_by=managed_by)
                if install:
                    yield install


# UV Specific finder
def get_uv_python_path() -> str | None:
    # Attempt to get cache
    try:
        with open(INSTALLER_CACHE_PATH) as f:
            installer_cache = _laz.json.load(f)
    except (FileNotFoundError, _laz.json.JSONDecodeError):
        installer_cache = {}

    uv_python_dir = installer_cache.get("uv")
    if uv_python_dir and os.path.exists(uv_python_dir):
        return uv_python_dir

    # Cache failed
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

    # Fill cache and update the cache file
    installer_cache["uv"] = uv_python_dir
    os.makedirs(os.path.dirname(INSTALLER_CACHE_PATH), exist_ok=True)
    with open(INSTALLER_CACHE_PATH, 'w') as f:
        _laz.json.dump(installer_cache, f)

    return uv_python_dir


def _implementation_from_uv_dir(
    direntry: os.DirEntry,
    finder: DetailFinder | None = None,
) -> PythonInstall | None:
    python_exe = "python.exe" if sys.platform == "win32" else "bin/python"
    python_path = os.path.join(direntry, python_exe)

    install: PythonInstall | None = None
    finder = DetailFinder() if finder is None else finder

    if os.path.exists(python_path):
        install = finder.get_install_details(python_path, managed_by="Astral")

    return install


def get_uv_pythons(finder=None) -> Iterator[PythonInstall]:
    # This takes some shortcuts over the regular pythonfinder
    # As the UV folders give the python version and the implementation
    if uv_python_path := get_uv_python_path():
        if os.path.exists(uv_python_path):
            finder = DetailFinder() if finder is None else finder

            with finder, os.scandir(uv_python_path) as fld:
                for f in fld:
                    if (
                        f.is_dir()
                        and (install := _implementation_from_uv_dir(f, finder=finder))
                    ):
                        yield install
