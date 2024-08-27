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
import os

from ducktools.lazyimporter import LazyImporter, ModuleImport, FromImport
from ducktools.pythonfinder import list_python_installs, __version__

_laz = LazyImporter(
    [
        ModuleImport("argparse"),
        ModuleImport("csv"),
        ModuleImport("subprocess"),
        ModuleImport("platform"),
        FromImport(".pythonorg_search", "PythonOrgSearch"),
        FromImport("packaging.specifiers", "SpecifierSet"),
        FromImport("urllib.error", "URLError"),
    ],
    globs=globals()
)


class UnsupportedPythonError(Exception):
    pass


def stop_autoclose():
    """
    Checks if it thinks windows will auto close the window after running

    The logic here is it checks if the PID of this task is running as py.exe

    By default py.exe is set as the runner for double-clicked .pyz files on
    windows.
    """
    autoclosing = False

    if sys.platform == "win32":
        exe_name = "py.exe"
        tasklist = _laz.subprocess.check_output(
            ["tasklist", "/v", "/fo", "csv", "/fi", f"PID eq {os.getppid()}"],
            text=True
        )
        data = _laz.csv.DictReader(tasklist.split("\n"))
        for entry in data:
            if entry["Image Name"] == exe_name:
                autoclosing = True
                break

    if autoclosing:
        _laz.subprocess.run("pause", shell=True)


def parse_args(args):
    parser = _laz.argparse.ArgumentParser(
        prog="ducktools-pythonfinder",
        description="Discover base Python installs",
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command", required=False)

    online = subparsers.add_parser(
        "online",
        help="Get links to binaries from python.org"
    )

    # Shared arguments
    for p in [parser, online]:
        p.add_argument("--min", help="Specify minimum Python version")
        p.add_argument("--max", help="Specify maximum Python version")
        p.add_argument("--compatible", help="Specify compatible Python version")

    online.add_argument(
        "--all-binaries",
        action="store_true",
        help="Provide *all* matching binaries and "
             "not just the latest minor versions"
    )
    online.add_argument(
        "--system",
        action="store",
        help="Get python installers for a different system (eg: Windows, Darwin, Linux)"
    )
    online.add_argument(
        "--machine",
        action="store",
        help="Get python installers for a different architecture (eg: AMD64, ARM64, x86)"
    )

    online.add_argument(
        "--prerelease",
        action="store_true",
        help="Include prerelease versions"
    )

    vals = parser.parse_args(args)

    return vals


def display_local_installs(min_ver=None, max_ver=None, compatible=None):
    if min_ver:
        min_ver = tuple(int(i) for i in min_ver.split("."))
    if max_ver:
        max_ver = tuple(int(i) for i in max_ver.split("."))
    if compatible:
        compatible = tuple(int(i) for i in compatible.split("."))

    installs = list_python_installs()
    headings = ["Python Version", "Executable Location"]
    max_executable_len = max(
        len(headings[1]), max(len(inst.executable) for inst in installs)
    )
    headings_str = f"| {headings[0]} | {headings[1]:<{max_executable_len}s} |"

    print("Discoverable Python Installs")
    if sys.platform == "win32":
        print("+ - Listed in the Windows Registry ")
        print("^ - This is a 32-bit Python install")
    if sys.platform != "win32":
        print("[] - This Python install is shadowed by another on Path")
    print("* - This is the active Python executable used to call this module")
    print("** - This is the parent Python executable of the venv used to call this module")
    print()
    print(headings_str)
    print(f"| {'-' * len(headings[0])} | {'-' * max_executable_len} |")
    for install in installs:
        if min_ver and install.version < min_ver:
            continue
        elif max_ver and install.version > max_ver:
            continue
        elif compatible:
            mismatch = False
            for i, val in enumerate(compatible):
                if val != install.version[i]:
                    mismatch = True
                    break
            if mismatch:
                continue

        version_str = install.version_str

        if sys.platform == "win32":
            if install.metadata.get("InWindowsRegistry"):
                version_str = f"+{version_str}"
            if install.architecture == "32bit":
                version_str = f"^{version_str}"

        if install.executable == sys.executable:
            version_str = f"*{version_str}"
        elif (
            sys.prefix != sys.base_prefix
            and os.path.commonpath([install.executable, sys.base_prefix]) == sys.base_prefix
        ):
            version_str = f"**{version_str}"

        if install.shadowed:
            version_str = f"[{version_str}]"

        print(f"| {version_str:>14s} | {install.executable:<{max_executable_len}s} |")


def display_remote_binaries(
        min_ver,
        max_ver,
        compatible,
        all_binaries,
        system,
        machine,
        prerelease
):
    specs = []
    if min_ver:
        specs.append(f">={min_ver}")
    if max_ver:
        specs.append(f"<{max_ver}")
    if compatible:
        specs.append(f"~={compatible}")

    spec = _laz.SpecifierSet(",".join(specs))

    searcher = _laz.PythonOrgSearch(system=system, machine=machine)
    if all_binaries:
        releases = searcher.all_matching_binaries(spec, prereleases=prerelease)
    else:
        releases = searcher.latest_minor_binaries(spec, prereleases=prerelease)

    headings = ["Python Version", "URL"]

    if releases:
        max_url_len = max(
            len(headings[1]), max(len(release.url) for release in releases)
        )
        headings_str = f"| {headings[0]} | {headings[1]:<{max_url_len}s} |"

        print(headings_str)
        print(f"| {'-' * len(headings[0])} | {'-' * max_url_len} |")

        for release in releases:
            print(f"| {release.version:>14s} | {release.url:<{max_url_len}s} |")
    else:
        print("No Python releases found matching specification")


def main():
    if sys.version_info < (3, 8):
        v = sys.version_info
        raise UnsupportedPythonError(
            f"Python {v.major}.{v.minor}.{v.micro} is not supported. "
            f"ducktools.pythonfinder requires Python 3.8 or later."
        )

    if sys.argv[1:]:
        vals = parse_args(sys.argv[1:])

        if vals.command == "online":
            system = vals.system if vals.system else _laz.platform.system()
            machine = vals.machine if vals.machine else _laz.platform.machine()
            try:
                display_remote_binaries(
                    vals.min,
                    vals.max,
                    vals.compatible,
                    vals.all_binaries,
                    system,
                    machine,
                    vals.prerelease,
                )
            except _laz.URLError:
                print("Could not connect to python.org")
        else:
            display_local_installs(vals.min, vals.max, vals.compatible)
    else:
        # No arguments to parse
        display_local_installs()

    stop_autoclose()


if __name__ == "__main__":
    main()
