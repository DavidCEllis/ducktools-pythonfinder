# Dependency listing code modified from python-readiness
# https://github.com/hauntsaninja/python_readiness/
# MIT License
#
# Copyright (c) 2024 hauntsaninja

# Part of ducktools-pythonfinder
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
#
import importlib.metadata
import sys
import sysconfig

from pathlib import Path


def get_dependencies():
    purelib = Path(sysconfig.get_paths()["purelib"])
    safe_path = sys.path if getattr(sys.flags, "safe_path", False) else sys.path[1:]
    context = importlib.metadata.DistributionFinder.Context(path=safe_path)
    for dist in importlib.metadata.distributions(context=context):
        if (
            isinstance(dist, importlib.metadata.PathDistribution)
            and (dist_path := getattr(dist, '_path', None))
            and isinstance(dist_path, Path)
            and not dist_path.is_relative_to(purelib)
        ):
            continue
        metadata = dist.metadata
        name, version = metadata["Name"], metadata["Version"]
        print(f"{name}=={version}")


if __name__ == "__main__":
    get_dependencies()
