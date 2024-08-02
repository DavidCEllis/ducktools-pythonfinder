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
import os.path
from unittest.mock import patch, MagicMock, call
import textwrap
import subprocess
from pathlib import Path

import pytest

from ducktools.pythonfinder.shared import (
    get_install_details,
    PythonInstall,
    get_folder_pythons,
)
from ducktools.pythonfinder import details_script

fake_details_out = PythonInstall(
    version=(3, 10, 11, "final", 0),
    executable="~/.pyenv/versions/3.10.11/python",
    architecture="64bit",
    implementation="cpython",
    metadata={},
)

fake_details = textwrap.dedent(
    """
    {
        "version": [3, 10, 11, "final", 0], 
        "executable": "~/.pyenv/versions/3.10.11/python", 
        "architecture": "64bit", 
        "implementation": "cpython", 
        "metadata": {}
    }
"""
)

details_text = Path(details_script.__file__).read_text()


@pytest.mark.parametrize(
    "output, expected", [(fake_details, fake_details_out), ("InvalidJSON", None)]
)
def test_get_install_details(output, expected):
    with patch("subprocess.run") as run_mock:
        mock_out = MagicMock()

        mock_out.stdout = output
        run_mock.return_value = mock_out

        details = get_install_details(fake_details_out.executable)

        run_mock.assert_called_with(
            [fake_details_out.executable, "-"],
            input=details_text,
            capture_output=True,
            text=True,
            check=True,
        )

        assert details == expected


def test_get_install_details_error():
    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "Unsuccessful Call"),
    ) as run_mock:
        details = get_install_details(fake_details_out.executable)

        run_mock.assert_called_with(
            [fake_details_out.executable, "-"],
            input=details_text,
            capture_output=True,
            text=True,
            check=True,
        )

        assert details is None


def test_get_folder_pythons(fs):
    func = "ducktools.pythonfinder.shared.get_install_details"

    if sys.platform == "win32":
        fld = "C:\\temp\\python"
        python_exe = os.path.join(fld, "python.exe")
        pypy_exe = os.path.join(fld, "pypy.exe")
        non_python_file = os.path.join(fld, "python3-futurize.exe")
    else:
        fld = "~/temp/python"
        python_exe = os.path.join(fld, "python")
        pypy_exe = os.path.join(fld, "pypy")
        non_python_file = os.path.join(fld, "python3-futurize")

    fs.create_dir(fld)

    fs.create_file(python_exe)
    fs.create_file(pypy_exe)
    fs.create_file(non_python_file)

    def mock_func(pth):
        return pth

    with patch(func, side_effect=mock_func) as get_dets:
        result = list(get_folder_pythons(fld))

        get_dets.assert_has_calls(
            [
                call(python_exe),
                call(pypy_exe),
            ],
            any_order=True,
        )

    assert result == [python_exe, pypy_exe]
