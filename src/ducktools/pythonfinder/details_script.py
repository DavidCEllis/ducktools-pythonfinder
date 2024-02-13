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
