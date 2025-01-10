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

import os
import re
import subprocess

from tempfile import TemporaryDirectory

import unittest.mock as mock


import pytest

from ducktools.pythonfinder.shared import (
    UV_PYTHON_RE,
    get_uv_python_path,
    get_uv_pythons,
)

UV_REASON = "UV is not installed - skipping tests that run UV"


@pytest.fixture
def uv_pythondir():
    # Set the UV python folder to a temporary folder and
    # yield the temporary folder value
    uv_python_envkey = "UV_PYTHON_INSTALL_DIR"
    old_uv_python_dir = os.environ.get(uv_python_envkey)
    try:
        with TemporaryDirectory() as tempdir:
            os.environ[uv_python_envkey] = tempdir
            yield tempdir
    finally:
        if old_uv_python_dir is None:
            del os.environ[uv_python_envkey]
        else:
            os.environ[uv_python_envkey] = old_uv_python_dir


class TestUVFakes:
    def test_fake_get_uv_python_path_success(self, uv_pythondir):
        # Test the subprocess is called correctly and returned correctly
        with mock.patch("subprocess.run") as run_mock:
            run_mock.return_value.stdout = f"{uv_pythondir}\n"

            pydir = get_uv_python_path()

            run_mock.assert_called_once_with(
                ["uv", "python", "dir"],
                check=True,
                text=True,
                capture_output=True,
            )

            assert pydir == uv_pythondir

    def test_fake_get_uv_python_path_failure(self, uv_pythondir):
        # Test the subprocess is called correctly and returned correctly
        with mock.patch("subprocess.run") as run_mock:
            run_mock.side_effect = subprocess.CalledProcessError(-1, "uv python dir")

            pydir = get_uv_python_path()

            run_mock.assert_called_once_with(
                ["uv", "python", "dir"],
                check=True,
                text=True,
                capture_output=True,
            )

            assert pydir is None

    def test_fake_get_uv_python_path_notfound(self, uv_pythondir):
        # Test the subprocess is called correctly and returned correctly
        with mock.patch("subprocess.run") as run_mock:
            run_mock.side_effect = FileNotFoundError("[Errno 2] No such file or directory: 'uv'")

            pydir = get_uv_python_path()

            run_mock.assert_called_once_with(
                ["uv", "python", "dir"],
                check=True,
                text=True,
                capture_output=True,
            )

            assert pydir is None


@pytest.mark.skipif(get_uv_python_path() is None, reason=UV_REASON)
class TestUVReal:
    def test_real_get_uv_python_path(self, uv_pythondir):
        # This checks the UV python path has actually been set
        uv_path = get_uv_python_path()
        assert uv_path == uv_pythondir

    def test_tempdir_empty(self, uv_pythondir):
        # Tempdir should not have any python installs initially
        pythons = list(get_uv_pythons())
        assert pythons == []

    @pytest.mark.uv_python
    def test_finds_installed_python(self, uv_pythondir):
        # Install python 3.12.6 in the tempdir
        subprocess.run(
            ["uv", "python", "install", "3.12.6"],
            check=True,
        )

        pythons = list(get_uv_pythons())
        assert len(pythons) == 1
        assert pythons[0].version_str == "3.12.6"
        assert pythons[0].implementation == "cpython"
        assert pythons[0].managed_by == "Astral UV"

    @pytest.mark.uv_python
    def test_finds_installed_pypy(self, uv_pythondir):
        subprocess.run(
            ["uv", "python", "install", "pypy3.10"],
            check=True,
        )

        pythons = list(get_uv_pythons())
        assert len(pythons) == 1
        assert pythons[0].version >= (3, 10, 14)
        assert pythons[0].implementation == "pypy"
        assert pythons[0].implementation_version >= (7, 3, 17)
        assert pythons[0].managed_by == "Astral UV"


def test_regex_matches():
    example_312 = "cpython-3.12.7-windows-x86_64-none"
    match = re.match(UV_PYTHON_RE, example_312)
    assert match.groups() == ("cpython", "3.12.7", "", "windows", "x86_64")

    example_313t = "cpython-3.13.0+freethreaded-windows-x86_64-none"
    match = re.match(UV_PYTHON_RE, example_313t)
    assert match.groups() == ("cpython", "3.13.0", "freethreaded", "windows", "x86_64")
