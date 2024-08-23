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

"""
Search the Windows registry to find python installs

Based on PEP 514 registry entries.
"""

import winreg  # noqa  # pycharm seems to think winreg doesn't exist in python3.12
from _collections_abc import Iterator

from ..shared import PythonInstall

exclude_companies = {
    "PyLauncher",  # pylauncher is special cased to be ignored
}


check_pairs = [
    # Keys defined in PEP 514
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Python", 0),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Python", winreg.KEY_WOW64_64KEY),
    # For system wide 32 bit python installs
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Python", winreg.KEY_WOW64_32KEY),
]


def enum_keys(key):
    subkey_count, _, _ = winreg.QueryInfoKey(key)
    for i in range(subkey_count):
        yield winreg.EnumKey(key, i)


def enum_values(key):
    _, value_count, _ = winreg.QueryInfoKey(key)
    for i in range(value_count):
        yield winreg.EnumValue(key, i)


def get_registered_pythons() -> Iterator[PythonInstall]:
    for base, py_folder, flags in check_pairs:
        base_key = None
        try:
            base_key = winreg.OpenKeyEx(base, py_folder, access=winreg.KEY_READ | flags)
        except FileNotFoundError:
            continue
        else:
            # Query the base folder eg: HKEY_LOCAL_MACHINE\SOFTWARE\Python
            # The values here should be "companies" as defined in the PEP
            for company in enum_keys(base_key):
                if company in exclude_companies:
                    continue

                with winreg.OpenKey(base_key, company) as company_key:
                    comp_metadata = {}

                    for name, data, _ in enum_values(company_key):
                        comp_metadata[f"Company{name}"] = data

                    for py_keyname in enum_keys(company_key):
                        metadata = {**comp_metadata}

                        with winreg.OpenKey(company_key, py_keyname) as py_key:
                            for name, data, _ in enum_values(py_key):
                                metadata[name] = data

                            install_key = None
                            try:
                                install_key = winreg.OpenKey(py_key, "InstallPath")
                                python_path, _ = winreg.QueryValueEx(
                                    install_key,
                                    "ExecutablePath",
                                )
                            except FileNotFoundError:
                                python_path = None
                            finally:
                                if install_key:
                                    winreg.CloseKey(install_key)

                            python_version: str | None = metadata.get("Version")
                            # Pyenv puts architecture information in the Version value for some reason
                            if python_version:
                                python_version = python_version.split("-")[0]

                            architecture = metadata.get("SysArchitecture")

                            metadata["InWindowsRegistry"] = True

                        if python_path and python_version:
                            try:
                                yield PythonInstall.from_str(
                                    version=python_version,
                                    executable=python_path,
                                    architecture=architecture,
                                    metadata=metadata,
                                )
                            except ValueError:
                                pass

        finally:
            if base_key:
                winreg.CloseKey(base_key)
