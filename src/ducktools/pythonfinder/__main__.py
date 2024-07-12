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


import sys

from ducktools.lazyimporter import LazyImporter, ModuleImport
from ducktools.pythonfinder import list_python_installs

_laz = LazyImporter([ModuleImport("argparse")])


def parse_args(args):
    parser = _laz.argparse.ArgumentParser(
        prog="ducktools-pythonfinder",
        description="Discover base Python installs",
    )
    parser.add_argument("--min", help="Specify minimum Python version")
    parser.add_argument("--max", help="Specify maximum Python version")
    parser.add_argument("--exact", help="Specify exact Python version")

    vals = parser.parse_args(args)

    if vals.min:
        min_ver = tuple(int(i) for i in vals.min.split("."))
    else:
        min_ver = None

    if vals.max:
        max_ver = tuple(int(i) for i in vals.max.split("."))
    else:
        max_ver = None

    if vals.exact:
        exact = tuple(int(i) for i in vals.exact.split("."))
    else:
        exact = None

    return min_ver, max_ver, exact


def main():
    if sys.argv[1:]:
        min_ver, max_ver, exact = parse_args(sys.argv[1:])
    else:
        min_ver, max_ver, exact = None, None, None

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
        if min_ver and install.version < min_ver:
            continue
        elif max_ver and install.version > max_ver:
            continue
        elif exact:
            mismatch = False
            for i, val in enumerate(exact):
                if val != install.version[i]:
                    mismatch = True
                    break
            if mismatch:
                continue

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
