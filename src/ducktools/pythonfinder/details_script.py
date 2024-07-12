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


def get_details():
    try:
        implementation = sys.implementation.name
    except AttributeError:  # pragma: no cover
        # Probably Python 2
        import platform

        implementation = platform.python_implementation().lower()
        metadata = {}
    else:
        if implementation != "cpython":  # pragma: no cover
            metadata = {"{}_version".format(implementation): sys.implementation.version}
        else:
            metadata = {}

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
