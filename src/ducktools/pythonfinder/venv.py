# ducktools-pythonfinder
# MIT License
# 
# Copyright (c) 2013-2014 David C Ellis
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
import sys


from ducktools.classbuilder.prefab import Prefab
from ducktools.lazyimporter import LazyImporter, FromImport, ModuleImport

from .shared import (
    PythonInstall,
    get_install_details,
    version_str_to_tuple,
    version_tuple_to_str,
)


_laz = LazyImporter(
    [
        ModuleImport("re"),
        ModuleImport("json"),
        FromImport("pathlib", "Path"),
        FromImport("subprocess", "run"),
    ]
)

VENV_CONFIG_NAME = "pyvenv.cfg"


# VIRTUALENV can make some invalid regexes that are just the tuple with dots.
VIRTUALENV_PY_VER_RE = (
    r"(?P<major>\d+)\.(?P<minor>\d+)\.?(?P<micro>\d*)\.(?P<releaselevel>.+)\.(?P<serial>\d*)?"
)


class PythonPackage(Prefab):
    name: str
    version: str


class PythonVEnv(Prefab):
    folder: str
    executable: str
    version: tuple[int, int, int, str, int]
    parent_path: str

    @property
    def version_str(self) -> str:
        return version_tuple_to_str(self.version)

    @property
    def parent_executable(self) -> str:
        if sys.platform == "win32":
            return os.path.join(self.parent_path, "python.exe")
        else:
            return os.path.join(self.parent_path, "python")

    @property
    def parent_exists(self) -> bool:
        return os.path.exists(self.parent_executable)

    def get_parent_install(self, cache: list[PythonInstall] | None = None) -> PythonInstall | None:
        install = None
        cache = [] if cache is None else cache

        if self.parent_exists:
            exe = self.parent_executable

            # Python installs may be cached, can skip querying exe.
            for inst in cache:
                if os.path.samefile(inst.executable, exe):
                    install = inst
                    break

            if install is None:
                install = get_install_details(exe)

        return install

    def list_packages(self):
        if not self.parent_exists:
            raise FileNotFoundError(
                f"Parent Python at \"{self.parent_executable}\" does not exist."
            )

        # Should probably use sys.executable and have pip as a dependency
        # We would need to look at possibly changing how ducktools-env works for that however.

        data = _laz.run(
            [
                self.parent_executable,
                "-m", "pip",
                "--python", self.executable,
                "list",
                "--format", "json"
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        raw_packages = _laz.json.loads(data.stdout)

        packages = [
            PythonPackage(
                name=p["name"],
                version=p["version"],
            )
            for p in raw_packages
        ]

        return packages


def get_python_venvs(base_dir=None, recursive=True):
    base_dir = os.getcwd() if base_dir is None else base_dir

    if recursive:
        glob_call = _laz.Path(base_dir).glob(f"**/{VENV_CONFIG_NAME}")
    else:
        glob_call = _laz.Path(base_dir).glob(f"*/{VENV_CONFIG_NAME}")

    for conf in glob_call:
        parent_path, version_str = None, None
        venv_base = conf.parent

        with conf.open() as f:
            for line in f:
                key, value = (item.strip() for item in line.split("="))

                if key == "home":
                    parent_path = value
                elif key in {"version", "version_info"}:
                    # venv and uv use different key names :)
                    version_str = value

                if parent_path and version_str:
                    break
            else:
                # Not a valid venv, ignore
                continue

        if sys.platform == "win32":
            venv_exe = os.path.join(venv_base, "Scripts", "python.exe")
        else:
            venv_exe = os.path.join(venv_base, "bin", "python")

        version_tuple = None
        try:
            version_tuple = version_str_to_tuple(version_str)
        except ValueError:  # pragma: no cover
            # Might be virtualenv putting in incorrect versions
            parsed_version = _laz.re.fullmatch(VIRTUALENV_PY_VER_RE, version_str)
            if parsed_version:
                major, minor, micro, releaselevel, serial = parsed_version.groups()
                version_tuple = (
                    int(major),
                    int(minor),
                    int(micro) if micro else 0,
                    releaselevel,
                    int(serial if serial != "" else 0),
                )

        if version_tuple is not None:
            yield PythonVEnv(
                folder=venv_base,
                executable=venv_exe,
                version=version_tuple,
                parent_path=parent_path
            )


def list_python_venvs(base_dir=None, recursive=True) -> list[PythonVEnv]:
    return list(get_python_venvs(base_dir=base_dir, recursive=recursive))
