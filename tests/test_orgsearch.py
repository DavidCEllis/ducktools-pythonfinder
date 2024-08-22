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

from packaging.specifiers import SpecifierSet
import pytest

from ducktools.pythonfinder.pythonorg_search import PythonOrgSearch, get_download_tags, UnsupportedError


@pytest.fixture(scope="module")
def website_caches(sources_folder):
    release_cache = (sources_folder / "release.json").read_text()
    release_file_cache = (sources_folder / "release_file.json").read_text()

    return release_cache, release_file_cache


@pytest.fixture(scope="class")
def searcher(website_caches):
    def make_org_search(system, machine):
        release_cache, release_file_cache = website_caches
        return PythonOrgSearch(
            release_page_cache=release_cache,
            release_file_page_cache=release_file_cache,
            system=system,
            machine=machine,
        )
    return make_org_search


def test_invalid_win_tags():
    with pytest.raises(UnsupportedError):
        get_download_tags("Windows", "InvalidPlatform")


def test_matching_versions(searcher):
    # This test is actually platform independent
    s = searcher("Windows", "AMD64")

    pre_39 = s.matching_versions(SpecifierSet("<3.9"))
    for release in pre_39:
        assert release.version_tuple < (3, 9)

    post_39 = s.matching_versions(SpecifierSet(">=3.9"))
    for release in post_39:
        assert release.version_tuple >= (3, 9)

    match_39 = s.matching_versions(SpecifierSet("~=3.9.0"))
    for release in match_39:
        assert release.version_tuple[:2] == (3, 9)


class TestWindows:
    system = "Windows"
    machine = "AMD64"

    def test_latest(self, searcher):
        s = searcher(self.system, self.machine)

        latest_312 = s.latest_binary_match(SpecifierSet("~=3.12.0"))
        assert latest_312.version == "3.12.5"

        before_312 = s.latest_binary_match(SpecifierSet("<3.12"))
        assert before_312.version == "3.11.9"

    def test_latest_bins(self, searcher):
        s = searcher(self.system, self.machine)

        latest_310 = s.latest_minor_binaries(SpecifierSet(">=3.10.0"))

        assert len(latest_310) == 3

        # Check releases in reverse order
        assert latest_310[0].version == "3.12.5"
        assert latest_310[1].version == "3.11.9"
        assert latest_310[2].version == "3.10.11"

    def test_all_matching_binaries(self, searcher):
        s = searcher(self.system, self.machine)

        all_bins = s.all_matching_binaries(SpecifierSet(">=3.8.0"))

        # releases of each minor version since 3.8
        # v3.9.3 was yanked for incompatibilities
        assert len(all_bins) == 52

    def test_all_bin_extensions(self, searcher):
        # Check all extensions provided match one of the supported set

        s = searcher(self.system, self.machine)
        all_bins = s.all_matching_binaries(SpecifierSet())

        tags = get_download_tags(s.system, s.machine)

        for v in all_bins:
            assert any(v.url.endswith(tag) for tag in tags)

    def test_prerelease(self, searcher):
        s = searcher(self.system, self.machine)
        match = s.latest_binary_match(SpecifierSet(">=3.12"), prereleases=True)
        assert match.version == "3.13.0rc1"
        assert match.is_prerelease is True


class TestMacOS:
    system = "Darwin"
    machine = "x86_64"

    def test_latest(self, searcher):
        s = searcher(self.system, self.machine)

        latest_312 = s.latest_binary_match(SpecifierSet("~=3.12.0"))
        assert latest_312.version == "3.12.5"

        before_312 = s.latest_binary_match(SpecifierSet("<3.12"))
        assert before_312.version == "3.11.9"

    def test_latest_bins(self, searcher):
        s = searcher(self.system, self.machine)

        latest_310 = s.latest_minor_binaries(SpecifierSet(">=3.10.0"))

        assert len(latest_310) == 3

        # Check releases in reverse order
        assert latest_310[0].version == "3.12.5"
        assert latest_310[1].version == "3.11.9"
        assert latest_310[2].version == "3.10.11"

    def test_all_matching_binaries(self, searcher):
        s = searcher(self.system, self.machine)

        all_bins = s.all_matching_binaries(SpecifierSet(">=3.8.0"))

        # releases of each minor version since 3.8
        # v3.9.3 was yanked for incompatibilities
        # MacOS has duplicates for Intel only binaries
        assert len(all_bins) == 64

    def test_all_bin_extensions(self, searcher):
        # Check all extensions provided match one of the supported set

        s = searcher(self.system, self.machine)
        all_bins = s.all_matching_binaries(SpecifierSet())

        tags = get_download_tags(s.system, s.machine)

        for v in all_bins:
            assert any(v.url.endswith(tag) for tag in tags)


class TestLinux:
    system = "Linux"
    machine = "x86_64"

    def test_latest(self, searcher):
        s = searcher(self.system, self.machine)

        latest_312 = s.latest_binary_match(SpecifierSet("~=3.12.0"))
        assert latest_312.version == "3.12.5"

        before_312 = s.latest_binary_match(SpecifierSet("<3.12"))
        assert before_312.version == "3.11.9"

    def test_latest_bins(self, searcher):
        s = searcher(self.system, self.machine)

        latest_310 = s.latest_minor_binaries(SpecifierSet(">=3.10.0"))

        assert len(latest_310) == 3

        # Check releases in reverse order
        assert latest_310[0].version == "3.12.5"
        assert latest_310[1].version == "3.11.9"
        assert latest_310[2].version == "3.10.14"  # source only release

    def test_all_matching_binaries(self, searcher):
        s = searcher(self.system, self.machine)

        all_bins = s.all_matching_binaries(SpecifierSet(">=3.8.0"))

        # releases of each minor version since 3.8
        # v3.9.3 was yanked for incompatibilities
        # Linux includes source releases and has multiple formats for them
        assert len(all_bins) == 140

    def test_all_bin_extensions(self, searcher):
        # Check all extensions provided match one of the supported set

        s = searcher(self.system, self.machine)
        all_bins = s.all_matching_binaries(SpecifierSet())

        tags = get_download_tags(s.system, s.machine)

        for v in all_bins:
            assert any(v.url.endswith(tag) for tag in tags)
