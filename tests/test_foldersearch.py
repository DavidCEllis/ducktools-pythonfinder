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
from unittest.mock import patch, MagicMock
import textwrap
import subprocess

import pytest

from ducktools.pythonfinder.shared import get_install_details, PythonInstall
from ducktools.pythonfinder import details_script

fake_details_out = PythonInstall(
    version=(3, 10, 11, "final", 0),
    executable="~/.pyenv/versions/3.10.11/python",
    architecture="64bit",
    implementation="cpython",
    metadata={},
)

fake_details = textwrap.dedent("""
    {
        "version": [3, 10, 11, "final", 0], 
        "executable": "~/.pyenv/versions/3.10.11/python", 
        "architecture": "64bit", 
        "implementation": "cpython", 
        "metadata": {}
    }
""")


@pytest.mark.parametrize("output, expected", [(fake_details, fake_details_out), ("InvalidJSON", None)])
def test_get_install_details(output, expected):
    with patch("ducktools.pythonfinder.shared._laz.subprocess.run") as run_mock:
        mock_out = MagicMock()

        mock_out.stdout = output
        run_mock.return_value = mock_out

        details = get_install_details(fake_details_out.executable)

        run_mock.assert_called_with(
            [fake_details_out.executable, details_script.__file__],
            capture_output=True,
            text=True,
            check=True,
        )

        assert details == expected


def test_get_install_details_error():
    with patch(
        "ducktools.pythonfinder.shared._laz.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "Unsuccessful Call")
    ) as run_mock:

        details = get_install_details(fake_details_out.executable)

        run_mock.assert_called_with(
            [fake_details_out.executable, details_script.__file__],
            capture_output=True,
            text=True,
            check=True,
        )

        assert details is None
