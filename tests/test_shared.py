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
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path

import pytest

from ducktools.pythonfinder.shared import PythonInstall

version_pairs = [
    ("3.12.2", (3, 12, 2, "final", 0)),
    ("3.13.0a1", (3, 13, 0, "alpha", 1)),
    ("3.13.0b1", (3, 13, 0, "beta", 1)),
    ("3.14.0rc2", (3, 14, 0, "candidate", 2)),
    ("3.8.12", (3, 8, 12, "final", 0)),
    ("2.7.18", (2, 7, 18, "final", 0)),
    ("2.7", (2, 7, 0, "final", 0)),
]


@pytest.mark.parametrize("vstring, vtuple", version_pairs)
def test_from_str(vstring, vtuple):
    null_exe = "/usr/bin/python"

    inst = PythonInstall.from_str(vstring, null_exe)

    assert inst.version == vtuple


@pytest.mark.parametrize("vstring, vtuple", version_pairs)
def test_to_str(vstring, vtuple):
    null_exe = "/usr/bin/python"

    inst = PythonInstall(vtuple, null_exe)

    if vstring.count(".") == 1:
        vstring += ".0"

    assert inst.version_str == vstring


def test_all_versions_parsed():
    # This is just a test to make sure all the existing python version strings
    # Parse and do not fail.

    python_versions = Path(__file__).parent / "sources" / "python_versions.txt"

    with open(python_versions) as f:
        for line in f:
            if line.startswith("#"):
                continue
            _ = PythonInstall.from_str(line.strip(), "/usr/bin/python")


def test_fail_version():
    with pytest.raises(ValueError):
        PythonInstall.from_str("3.12.1.2", "/usr/bin/python")


def test_pip_version():
    with patch("subprocess.run") as mock_run:
        return_obj = SimpleNamespace(
            returncode=0,
            stdout="23.0.1",
        )

        mock_run.return_value = return_obj

        inst = PythonInstall(tuple(sys.version_info), sys.executable)

        pip_ver = inst.get_pip_version()

        mock_run.assert_called_once_with(
            [sys.executable, "-c", "import pip; print(pip.__version__, end='')"],
            text=True,
            capture_output=True,
        )

        assert pip_ver == "23.0.1"


def test_fail_pip_version():
    with patch("subprocess.run") as mock_run:
        return_obj = SimpleNamespace(
            returncode=1,
            stdout="23.0.1",
        )

        mock_run.return_value = return_obj

        inst = PythonInstall(tuple(sys.version_info), sys.executable)

        pip_ver = inst.get_pip_version()

        mock_run.assert_called_once_with(
            [sys.executable, "-c", "import pip; print(pip.__version__, end='')"],
            text=True,
            capture_output=True,
        )

        assert pip_ver is None
