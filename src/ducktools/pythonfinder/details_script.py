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

"""
Get the details from a python install as JSON
"""
import sys

FULL_PY_VER_RE = r"(?P<major>\d+)\.(?P<minor>\d+)\.?(?P<micro>\d*)-?(?P<releaselevel>a|b|c|rc)?(?P<serial>\d*)?"


def version_str_to_tuple(version):
    # Needed to parse GraalPy versions only available as strings
    import re

    parsed_version = re.fullmatch(FULL_PY_VER_RE, version)

    major, minor, micro, releaselevel, serial = parsed_version.groups()

    if releaselevel in {"a", "dev"}:
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


def get_details():
    try:
        implementation = sys.implementation.name
    except AttributeError:  # pragma: no cover
        # Probably Python 2
        import platform

        implementation = platform.python_implementation().lower()
        metadata = {}
    else:
        if implementation == "graalpy":
            # Special case GraalPy as it erroneously reports the CPython target
            # instead of the Graal versiion
            try:
                ver = __graalpython__.get_graalvm_version()
                metadata = {
                    "graalpy_version": version_str_to_tuple(ver)
                }
            except NameError:
                metadata = {"{}_version".format(implementation): sys.implementation.version}
        elif implementation != "cpython":  # pragma: no cover
            metadata = {"{}_version".format(implementation): sys.implementation.version}
        else:
            metadata = {}
            if sys.version_info >= (3, 13):
                import sysconfig
                freethreaded = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
                metadata["freethreaded"] = freethreaded


    install = dict(
        version=list(sys.version_info),
        executable=sys.executable,
        architecture="64bit" if (sys.maxsize > 2**32) else "32bit",
        implementation=implementation,
        metadata=metadata,
    )

    return install


def main():
    import json

    install = get_details()

    sys.stdout.write(json.dumps(install))


if __name__ == "__main__":  # pragma: no cover
    main()
