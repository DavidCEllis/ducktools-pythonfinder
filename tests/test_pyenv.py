import sys
import os
import os.path
from tempfile import TemporaryDirectory

import pytest
from unittest.mock import patch, Mock

from ducktools.pythonfinder.shared import PythonInstall

if sys.platform == "win32":
    from ducktools.pythonfinder.win32.pyenv_search import get_pyenv_pythons, PYENV_VERSIONS_FOLDER
else:
    from ducktools.pythonfinder.linux.pyenv_search import get_pyenv_pythons, PYENV_VERSIONS_FOLDER


def test_no_versions_folder():
    with patch("os.path.exists") as exists_mock:
        exists_mock.return_value = False
        assert get_pyenv_pythons() == []


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

        python_versions = get_pyenv_pythons()

    assert python_versions == [PythonInstall.from_str(out_ver, out_executable)]


@pytest.mark.skipif(sys.platform != "win32", reason="Test for Windows only")
def test_temp_versions_win():
    # Test with real temporary folders

    with TemporaryDirectory() as tmpdir:
        py_folder = os.path.join(tmpdir, "3.12.1")
        py_exe = os.path.join(py_folder, "python.exe")

        os.mkdir(py_folder)

        # make python.exe file
        with open(py_exe, "wb") as _:
            pass

        versions = get_pyenv_pythons(tmpdir)

        assert versions == [PythonInstall.from_str("3.12.1", py_exe)]


# @pytest.mark.skipif(os.environ.get("CI", False), reason="Don't make temporary folders in CI")
@pytest.mark.skipif(sys.platform == "win32", reason="Test for non-Windows only")
def test_temp_versions_non_win():
    # Test with real temporary folders

    with TemporaryDirectory() as tmpdir:
        py_folder = os.path.join(tmpdir, "3.12.1")
        py_exe = os.path.join(py_folder, "bin/python")

        os.mkdir(py_folder)
        os.mkdir(os.path.join(py_folder, "bin"))

        # make python.exe file
        with open(py_exe, "wb") as _:
            pass

        versions = get_pyenv_pythons(tmpdir)

        assert versions == [PythonInstall.from_str("3.12.1", py_exe)]
