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
from pathlib import Path

import pytest

from ducktools.pythonfinder import details_script


@pytest.fixture(scope="session")
def sources_folder():
    return Path(__file__).parent / "sources"


@pytest.fixture
def uses_details_script(fs):
    fs.add_real_file(details_script.__file__)


def pytest_addoption(parser):
    parser.addoption(
        "--run-uv-python",
        action="store_true",
        default=False,
        help="Run tests that involve installing UV pythons",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "uv_python: only run test if --run-uv-python is specified"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-uv-python"):
        skipper = pytest.mark.skip(reason="Only run when --run-uv-python is given")
        for item in items:
            if "uv_python" in item.keywords:
                item.add_marker(skipper)
