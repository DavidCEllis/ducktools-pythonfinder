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
import os.path
import textwrap
from pathlib import Path

import pytest
from unittest.mock import patch, Mock

from ducktools.pythonfinder.shared import PythonInstall
from ducktools.pythonfinder import details_script

if sys.platform == "win32":
    from ducktools.pythonfinder.win32.pyenv_search import (
        get_pyenv_pythons,
        PYENV_VERSIONS_FOLDER,
    )
else:
    from ducktools.pythonfinder.linux.pyenv_search import (
        get_pyenv_pythons,
        PYENV_VERSIONS_FOLDER,
    )


details_text = Path(details_script.__file__).read_text()


def test_no_versions_folder():
    with patch("os.path.exists") as exists_mock:
        exists_mock.return_value = False
        assert list(get_pyenv_pythons()) == []


def test_mock_versions_folder():
    mock_dir_entry = Mock(os.DirEntry)

    out_ver = "3.12.1"
    if sys.platform == "win32":
        out_executable = os.path.join(PYENV_VERSIONS_FOLDER, out_ver, "python.exe")
    else:
        out_executable = os.path.join(PYENV_VERSIONS_FOLDER, out_ver, "bin/python")

    mock_dir_entry.name = out_ver
    mock_dir_entry.path = os.path.join(PYENV_VERSIONS_FOLDER, out_ver)

    with patch("os.path.exists") as exists_mock, patch("os.scandir") as scandir_mock:
        exists_mock.return_value = True
        scandir_mock.return_value = iter([mock_dir_entry])

        python_versions = list(get_pyenv_pythons())

    assert python_versions == [PythonInstall.from_str(out_ver, out_executable)]


@pytest.mark.skipif(sys.platform != "win32", reason="Test for Windows only")
def test_fs_versions_win(fs):
    # Test with folders in fake file system

    tmpdir = "c:\\fake_folder"

    py_folder = os.path.join(tmpdir, "3.12.1")
    py_exe = os.path.join(py_folder, "python.exe")

    fs.create_dir(py_folder)
    fs.create_file(py_exe)

    versions = list(get_pyenv_pythons(tmpdir))

    assert versions == [PythonInstall.from_str("3.12.1", py_exe)]


@pytest.mark.skipif(sys.platform != "win32", reason="Test for Windows only")
def test_32bit_version(fs):
    # Test with folders in fake file system

    tmpdir = "c:\\fake_folder"

    py_folder = os.path.join(tmpdir, "3.12.1-win32")
    py_exe = os.path.join(py_folder, "python.exe")

    fs.create_dir(py_folder)
    fs.create_file(py_exe)

    versions = list(get_pyenv_pythons(tmpdir))

    assert versions == [PythonInstall.from_str("3.12.1", py_exe, architecture="32bit")]


@pytest.mark.skipif(sys.platform != "win32", reason="Test for Windows only")
def test_invalid_ver_win(fs):
    # Ignore non-standard versions

    tmpdir = "c:\\fake_folder"

    py_folder = os.path.join(tmpdir, "external-python3.12.1")
    py_exe = os.path.join(py_folder, "python.exe")

    fs.create_dir(py_folder)
    fs.create_file(py_exe)

    py2_folder = os.path.join(tmpdir, "ext3.13.0")
    py2_exe = os.path.join(py2_folder, "python.exe")

    fs.create_dir(py2_folder)
    fs.create_file(py2_exe)

    py3_folder = os.path.join(tmpdir, "invalid-version-3.12.1")
    py3_exe = os.path.join(py3_folder, "python.exe")

    fs.create_dir(py3_folder)
    fs.create_file(py3_exe)

    versions = list(get_pyenv_pythons(tmpdir))

    assert versions == []


@pytest.mark.skipif(sys.platform == "win32", reason="Test for non-Windows only")
def test_fs_versions_nix(fs):
    # Test folders in fake file system

    tmpdir = "~/.pyenv/versions"

    py_folder = os.path.join(tmpdir, "3.12.1")
    py_exe = os.path.join(py_folder, "bin/python")

    fs.create_dir(py_folder)
    fs.create_dir(os.path.join(py_folder, "bin"))
    fs.create_file(py_exe)

    versions = list(get_pyenv_pythons(tmpdir))

    assert versions == [PythonInstall.from_str("3.12.1", py_exe)]


@pytest.mark.skipif(sys.platform == "win32", reason="Test for non-Windows only")
def test_invalid_ver_nix(fs):
    # Test folders in fake file system

    tmpdir = "~/.pyenv/versions"

    py_folder = os.path.join(tmpdir, "external-python3.12.1")
    py_exe = os.path.join(py_folder, "bin/python")

    fs.create_dir(py_folder)
    fs.create_dir(os.path.join(py_folder, "bin"))
    fs.create_file(py_exe)

    py2_folder = os.path.join(tmpdir, "ext3.13.0")
    py2_exe = os.path.join(py2_folder, "bin/python")

    fs.create_dir(py2_folder)
    fs.create_dir(os.path.join(py2_folder, "bin"))
    fs.create_file(py2_exe)

    py3_folder = os.path.join(tmpdir, "invalid-version-3.12.1")
    py3_exe = os.path.join(py3_folder, "bin/python")

    fs.create_dir(py3_folder)
    fs.create_dir(os.path.join(py3_folder, "bin"))
    fs.create_file(py3_exe)

    versions = list(get_pyenv_pythons(tmpdir))

    assert versions == []


@pytest.mark.skipif(sys.platform == "win32", reason="Test for non-Windows only")
def test_pypy_version(fs):
    # Test pypy version retrieval

    ver_folder = "pypy3.10-7.3.15"
    tmpdir = "~/.pyenv/versions"

    mock_output = textwrap.dedent(
        """
        {"version": [3, 10, 13, "final", 0],
        "executable": "~/.pyenv/versions/pypy3.10-7.3.15/bin/pypy",
        "architecture": "64bit",
        "implementation": "pypy",
        "metadata": {"pypy_version": [7, 3, 15, "final", 0]}}
        """
    ).strip()

    py_folder = os.path.join(tmpdir, ver_folder)
    py_exe = os.path.join(py_folder, "bin/python")

    fs.create_dir(py_folder)
    fs.create_dir(os.path.join(py_folder, "bin"))
    fs.create_file(py_exe)

    with patch("subprocess.run") as run_cmd:
        run_cmd.return_value.stdout = mock_output
        versions = list(get_pyenv_pythons(tmpdir))

        run_cmd.assert_called_once_with(
            [py_exe, "-"],
            input=details_text,
            capture_output=True,
            text=True,
            check=True,
        )

        out_version = PythonInstall(
            version=(3, 10, 13, "final", 0),
            executable="~/.pyenv/versions/pypy3.10-7.3.15/bin/pypy",
            architecture="64bit",
            implementation="pypy",
            metadata={"pypy_version": (7, 3, 15, "final", 0)},
        )

        assert versions == [out_version]
