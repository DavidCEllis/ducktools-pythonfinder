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
import sys

from unittest.mock import patch

import json

from ducktools.pythonfinder.details_script import main, get_details


def test_details_script():
    with patch("sys.stdout.write") as mock:
        details = get_details()

        main()

        # Check the correct thing is being written to stdout
        mock.assert_called_with(json.dumps(details))

        result = json.loads(mock.mock_calls[0].args[0])

        # Check it recovers correctly
        for key in details:
            if key == "metadata":
                # Skip metadata
                continue

            assert result[key] == details[key]
