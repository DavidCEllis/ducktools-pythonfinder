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

from ducktools.pythonfinder import list_python_installs

import sys


def main():
    installs = list_python_installs()
    headings = ["Python Version", "Executable Location"]
    max_executable_len = max(
        len(headings[1]), max(len(inst.executable) for inst in installs)
    )
    headings_str = f"| {headings[0]} | {headings[1]:<{max_executable_len}s} |"

    print("Discoverable Python Installs")
    if sys.platform == "win32":
        print("+ - Listed in the Windows Registry ")
    print("* - This is the active python executable used to call this module")
    print(
        "** - This is the parent python executable of the venv used to call this module"
    )
    print()
    print(headings_str)
    print(f"| {'-' * len(headings[0])} | {'-' * max_executable_len} |")
    for install in installs:
        version_str = install.version_str
        if install.executable == sys.executable:
            version_str = f"*{version_str}"
        elif sys.prefix != sys.base_prefix and install.executable.startswith(
            sys.base_prefix
        ):
            version_str = f"**{version_str}"

        if sys.platform == "win32" and install.metadata.get("InWindowsRegistry"):
            version_str = f"+{version_str}"

        print(f"| {version_str:>14s} | {install.executable:<{max_executable_len}s} |")


main()
