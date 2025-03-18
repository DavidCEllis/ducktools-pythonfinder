# ducktools-pythonfinder
# MIT License
# 
# Copyright (c) 2025 David C Ellis
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
import os.path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ducktools.pythonfinder.shared import DetailFinder, PythonInstall

fake_python_path = "/path/to/python"
example_json = """
{
    "version": [3, 13, 2, "final", 0], 
    "executable": "/path/to/python", 
    "architecture": "64bit", 
    "implementation": "cpython", 
    "metadata": {"freethreaded": false}
}
""".strip()

example_install = PythonInstall(
    version=(3, 13, 2, "final", 0),
    executable=fake_python_path,
    architecture="64bit",
    implementation="cpython",
    metadata={"freethreaded": False}
)


@pytest.fixture
def run_mock():
    with patch("subprocess.run") as mock:
        mock.return_value.stdout = example_json
        yield mock


@pytest.fixture
def stat_mock():
    result = SimpleNamespace(
        st_mode=33279,
        st_ino=6755399441550587,
        st_dev=7836505329022787966,
        st_nlink=1,
        st_uid=0,
        st_gid=0,
        st_size=91648,
        st_atime=1741351198,
        st_mtime=1739886571,
        st_ctime=1739886571
    )

    with patch("os.stat") as mock:
        mock.return_value = result
        yield


def test_run(run_mock, temp_finder):
    with temp_finder:
        result = temp_finder.query_install(fake_python_path)

    assert result == example_install


def test_save_on_exit(run_mock, stat_mock, temp_finder):
    with patch.object(DetailFinder, "save") as save_mock:
        with temp_finder:
            details = temp_finder.get_install_details(fake_python_path)

        assert details == example_install
        save_mock.assert_called()


def test_save_only_if_changed(run_mock, stat_mock, temp_finder):
    with patch.object(DetailFinder, "save") as save_mock:
        with temp_finder:
            details = temp_finder.get_install_details(fake_python_path)

        assert details == example_install
        save_mock.assert_called()
        save_mock.reset_mock()
        temp_finder._dirty_cache = False  # This would be reset by save

        # Should fetch from cache and not call the save mock again
        with temp_finder:
            details = temp_finder.get_install_details(fake_python_path)

        assert details == example_install

        save_mock.assert_not_called()


def test_save_only_final_exit(run_mock, stat_mock, temp_finder):
    with patch.object(DetailFinder, "save") as save_mock:
        with temp_finder:
            with temp_finder:
                details = temp_finder.get_install_details(fake_python_path)
                assert details == example_install
            # Exit 1 level, should not call save yet
            save_mock.assert_not_called()
        # Full exit, should be called
        save_mock.assert_called()

def test_clear_cache(run_mock, stat_mock, temp_finder):
    with patch.object(DetailFinder, "save") as save_mock:
        with temp_finder:
            details = temp_finder.get_install_details(fake_python_path)

        assert details == example_install
        save_mock.assert_called()
        save_mock.reset_mock()
        temp_finder._dirty_cache = False  # This would be reset by save

        # Clear the cache
        with temp_finder:
            temp_finder.clear_cache()

        save_mock.assert_called()
        save_mock.reset_mock()
        temp_finder._dirty_cache = False  # This would be reset by save

        # Cache cleared, should get the details again and save
        with temp_finder:
            details = temp_finder.get_install_details(fake_python_path)

        assert details == example_install

        save_mock.assert_called()

def test_clear_invalid_runtimes(run_mock, stat_mock, temp_finder):
    with patch.object(DetailFinder, "save") as save_mock:
        # First fill cache
        with temp_finder:
            temp_finder.get_install_details(fake_python_path)

        save_mock.assert_called()
        save_mock.reset_mock()
        temp_finder._dirty_cache = False  # This would be reset by save

        with temp_finder, patch("os.path.exists") as exists_patch:
            exists_patch.return_value = True
            temp_finder.clear_invalid_runtimes()
        
        save_mock.assert_not_called()
        assert os.path.abspath(fake_python_path) in temp_finder.raw_cache

        with temp_finder, patch("os.path.exists") as exists_patch:
            exists_patch.return_value = False
            temp_finder.clear_invalid_runtimes()

        save_mock.assert_called()
        assert os.path.abspath(fake_python_path) not in temp_finder.raw_cache


def test_changed_stat_invalidates(run_mock, temp_finder):
    fake_abspath = os.path.abspath(fake_python_path)

    result = SimpleNamespace(
        st_mode=33279,
        st_ino=6755399441550587,
        st_dev=7836505329022787966,
        st_nlink=1,
        st_uid=0,
        st_gid=0,
        st_size=91648,
        st_atime=1741351198,
        st_mtime=1739886571,
        st_ctime=1739886571
    )
    changed_result = SimpleNamespace(
        st_mode=33279,
        st_ino=6755399441550587,
        st_dev=7836505329022787966,
        st_nlink=1,
        st_uid=0,
        st_gid=0,
        st_size=91648,
        st_atime=1741351198,
        st_mtime=1739886572,
        st_ctime=1739886571
    )

    with patch.object(DetailFinder, "save"):
        with patch("os.stat") as statmock, patch.object(DetailFinder, "query_install") as querymock:
            statmock.return_value = result
            querymock.return_value = example_install

            with temp_finder:
                details = temp_finder.get_install_details(fake_python_path)

            assert temp_finder.raw_cache[fake_abspath]["mtime"] == 1739886571

            querymock.assert_called_with(fake_abspath, None, None)
            querymock.reset_mock()

            with temp_finder:
                details = temp_finder.get_install_details(fake_python_path)

            assert temp_finder.raw_cache[fake_abspath]["mtime"] == 1739886571
            querymock.assert_not_called()

            statmock.return_value = changed_result
            with temp_finder:
                details = temp_finder.get_install_details(fake_python_path)

            assert temp_finder.raw_cache[fake_abspath]["mtime"] == 1739886572
            querymock.assert_called()