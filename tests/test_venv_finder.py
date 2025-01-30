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
import subprocess
import sys
import tempfile

from ducktools.pythonfinder.venv import list_python_venvs

import pytest


@pytest.fixture(scope="module")
def with_venvs():
    with tempfile.TemporaryDirectory() as tmpdir:
        # We can't actually use venv directly here as
        # Older python on linux makes invalid venvs
        if sys.platform == "win32":
            python_exe = os.path.join(sys.base_prefix, "python.exe")
        else:
            python_exe = os.path.join(sys.base_prefix, "bin", "python")

        def make_venv(pth):
            subprocess.run(
                [
                    python_exe,
                    "-m", "venv",
                    "--without-pip",
                    os.path.join(tmpdir, pth),
                ],
                check=True,
                capture_output=True
            )

        make_venv(".venv")
        make_venv("subfolder/.venv")
        make_venv("subfolder/subsubfolder/env")

        assert os.path.exists(os.path.join(tmpdir, ".venv"))

        yield tmpdir


def test_no_venvs():
    # Don't use the venv directory here
    with tempfile.TemporaryDirectory() as tmpdir:
        venvs = list_python_venvs(base_dir=tmpdir)

    assert len(venvs) == 0


def test_local_found(with_venvs):
    venvs = list_python_venvs(base_dir=with_venvs, recursive=False)

    assert len(venvs) == 1
    assert os.path.samefile(venvs[0].folder, os.path.join(with_venvs, ".venv"))


def test_parent_not_always_searched(with_venvs):
    venvs = list_python_venvs(base_dir=os.path.join(with_venvs, "subfolder"), search_parent_folders=False)

    assert len(venvs) == 1
    assert os.path.samefile(venvs[0].folder, os.path.join(with_venvs, "subfolder/.venv"))


def test_found_in_parent(with_venvs):
    venvs = list_python_venvs(base_dir=os.path.join(with_venvs, "subfolder"), search_parent_folders=True)

    assert os.path.samefile(venvs[0].folder, os.path.join(with_venvs, "subfolder/.venv"))
    assert os.path.samefile(venvs[1].folder, os.path.join(with_venvs, ".venv"))


def test_all_found(with_venvs):
    venvs = sorted(
        list_python_venvs(base_dir=with_venvs, recursive=True),
        key=lambda x: x.folder
    )

    assert len(venvs) == 3
    assert os.path.samefile(venvs[0].folder, os.path.join(with_venvs, ".venv"))
    assert os.path.samefile(venvs[1].folder, os.path.join(with_venvs, "subfolder/.venv"))
    assert os.path.samefile(venvs[2].folder, os.path.join(with_venvs, "subfolder/subsubfolder/env"))


def test_recursive_parents(with_venvs):
    venvs = sorted(
        list_python_venvs(
            base_dir=os.path.join(with_venvs, "subfolder"),
            recursive=True,
            search_parent_folders=True,
        ),
        key=lambda x: x.folder
    )

    assert len(venvs) == 3
    assert os.path.samefile(venvs[0].folder, os.path.join(with_venvs, ".venv"))
    assert os.path.samefile(venvs[1].folder, os.path.join(with_venvs, "subfolder/.venv"))
    assert os.path.samefile(venvs[2].folder, os.path.join(with_venvs, "subfolder/subsubfolder/env"))


def test_found_parent(with_venvs, this_python, this_venv):
    venv_ex = list_python_venvs(base_dir=with_venvs, recursive=False)[0]

    assert os.path.samefile(this_python.executable, venv_ex.parent_executable)

    # We found the base env that created this python, all details match
    parent = venv_ex.get_parent_install()
    assert os.path.dirname(parent.executable) == os.path.dirname(this_python.executable)

    # venv version str works same as parent
    assert venv_ex.version_str == parent.version_str


def test_found_parent_cache(with_venvs, this_python):
    venv_ex = list_python_venvs(base_dir=with_venvs, recursive=False)[0]

    parent = venv_ex.get_parent_install(cache=[this_python])
    assert parent == this_python


def test_empty_packages(with_venvs):
    venv_ex = list_python_venvs(base_dir=with_venvs, recursive=False)[0]

    assert os.path.exists(venv_ex.parent_executable)
    assert os.path.exists(venv_ex.executable)

    packages = venv_ex.list_packages()
    assert packages == []
