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

import sys

if sys.version_info < (3, 12):
    raise RuntimeError("This script requires Python 3.12 or newer.")

from collections.abc import Iterable, Callable, Generator
from pathlib import Path

from ducktools.classbuilder.prefab import Prefab
from ducktools.pythonfinder.venv import get_python_venvs


# Taken from ducktools-env's main
def get_columns(
    *,
    data: Iterable,
    headings: list[str],
    attributes: list[str],
    getter: Callable[[object, str], str] = getattr,
) -> Generator[str]:
    """
    A helper function to generate a table to print with correct column widths

    :param data: input data
    :param headings: headings for the top of the table
    :param attributes: attribute names to use for each column
    :param getter: attribute getter function (ex: getattr, dict.get)
    :return: Generator of column lines
    """
    if len(headings) != len(attributes):
        raise TypeError("Must be the same number of headings as attributes")

    widths = {
        f"{attrib}": len(head) for attrib, head in zip(attributes, headings)
    }

    data_rows = []
    for d in data:
        row = []
        for attrib in attributes:
            d_text = f"{getter(d, attrib)}"
            d_len = len(d_text)
            widths[f"{attrib}"] = max(widths[attrib], d_len)
            row.append(d_text)
        data_rows.append(row)

    yield (
        "| "
        + " | ".join(f"{head:<{widths[attrib]}}"
                     for head, attrib in zip(headings, attributes))
        + " |"
    )
    yield (
        "| "
        + " | ".join("-" * widths[attrib]
                     for attrib in attributes)
        + " |"
    )

    for row in data_rows:
        yield (
            "| "
            + " | ".join(f"{item:<{widths[attrib]}}"
                         for item, attrib in zip(row, attributes))
            + " |"
        )


class DisplayVEnv(Prefab):
    version: str
    path: str
    parent_path: str


def get_all_venvs():
    cwd = Path.cwd()

    venvs = get_python_venvs(recursive=True, search_parent_folders=True)
    venv_data = [
        DisplayVEnv(
            version=venv.version_str,
            path=str(Path(venv.folder).relative_to(cwd, walk_up=True)),
            parent_path=venv.parent_path,
        )
        for venv in venvs
    ]

    headings = ["Version", "Path", "Base Runtime"]
    attribs = ["version", "path", "parent_path"]

    for row in get_columns(data=venv_data, headings=headings, attributes=attribs, getter=getattr):
        print(row)


if __name__ == "__main__":
    get_all_venvs()
