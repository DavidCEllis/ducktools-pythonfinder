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

                            python_version = metadata.get("Version")
                            architecture = metadata.get("SysArchitecture")

                            metadata["InWindowsRegistry"] = True

                        if python_path and python_version:
                            yield PythonInstall.from_str(
                                version=python_version,
                                executable=python_path,
                                architecture=architecture,
                                metadata=metadata,
                            )

        finally:
            if base_key:
                winreg.CloseKey(base_key)
