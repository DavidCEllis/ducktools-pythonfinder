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

from ducktools.pythonfinder import get_python_installs


def main():
    installs = get_python_installs()
    headings = ["Python Version", "Executable Location"]
    max_executable_len = max(
        len(headings[1]), max(len(inst.executable) for inst in installs)
    )
    headings_str = f"| {headings[0]} | {headings[1]:<{max_executable_len}s} |"

    print(headings_str)
    print(f"| {'-' * len(headings[0])} | {'-' * max_executable_len} |")
    for install in get_python_installs():
        print(
            f"| {install.version_str:>14s} | {install.executable:<{max_executable_len}s} |"
        )


main()
