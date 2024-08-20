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

"""
This module searches python.org for a download link to the latest satisfactory
python version that includes a binary.

Currently only windows is supported, but macos will be supported as binaries also exist.
"""
from __future__ import annotations

import json
import platform

from urllib.request import urlopen

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from ducktools.classbuilder.prefab import Prefab, attribute, get_attributes
from ducktools.pythonfinder.shared import version_str_to_tuple


RELEASE_PAGE = "https://www.python.org/api/v2/downloads/release/"
RELEASE_FILE_PAGE = "https://www.python.org/api/v2/downloads/release_file/"


class UnsupportedError(Exception):
    pass


def get_binary_tags() -> list[str]:
    uname = platform.uname()
    if uname.system != "Windows":
        raise UnsupportedError(
            f"ducktools.pythonfinder does not support searching for binary installers on {uname.system!r}"
        )

    machine_tags = {
        "AMD64": "amd64",
        "ARM64": "arm64",
        "x86": ""
    }

    installer_extensions = [
        "-{machine_tag}.exe",
        ".{machine_tag}.msi",
    ]

    try:
        machine_tag = machine_tags[uname.machine]
    except KeyError:
        raise UnsupportedError(
            f"python.org does not provide binary installers for {uname.system!r} on {uname.machine!r}"
        )

    return [item.format(machine_tag=machine_tag) for item in installer_extensions]


# This code will move to shared
class PythonRelease(Prefab):
    name: str
    slug: str
    version: int
    is_published: bool
    is_latest: bool
    release_date: str
    pre_release: bool
    release_page: None  # Apparently this is always null?
    release_notes_url: str
    show_on_download_page: bool
    resource_uri: str
    _version_tuple: tuple | None = attribute(default=None, private=True)
    _version_spec: Version | None = attribute(default=None, private=True)

    @property
    def version_str(self):
        return self.name.split(" ")[1]

    @property
    def version_tuple(self):
        if self._version_tuple is None:
            self._version_tuple = version_str_to_tuple(self.version_str)
        return self._version_tuple

    @property
    def version_spec(self):
        if self._version_spec is None:
            self._version_spec = Version(self.version_str)
        return self._version_spec

    @property
    def is_prerelease(self):
        return self.version_spec.is_prerelease

    @classmethod
    def from_dict(cls, dict_data: dict):
        # Filter out any extra keys
        init_attribs = {k for k, v in get_attributes(cls).items() if v.init}
        key_dict = {
            k: v for k, v in dict_data.items()
            if k in init_attribs
        }
        return cls(**key_dict)


class PythonReleaseFile(Prefab):
    name: str
    slug: str
    os: str
    release: str
    description: str
    is_source: str
    url: str
    gpg_signature_file: str
    md5_sum: str
    filesize: int
    download_button: bool
    resource_uri: str
    sigstore_signature_file: str
    sigstore_cert_file: str
    sigstore_bundle_file: str
    sbom_spdx2_file: str

    @classmethod
    def from_dict(cls, dict_data: dict):
        # Filter out any extra keys
        init_attribs = {k for k, v in get_attributes(cls).items() if v.init}
        key_dict = {
            k: v for k, v in dict_data.items()
            if k in init_attribs
        }
        return cls(**key_dict)


class PythonDownload(Prefab):
    name: str
    version: str
    url: str
    md5_sum: str  # Python.org only provides md5 hash
    _version_tuple: tuple | None = attribute(default=None, private=True)
    _version_spec: Version | None = attribute(default=None, private=True)

    @property
    def version_tuple(self):
        if self._version_tuple is None:
            self._version_tuple = version_str_to_tuple(self.version)
        return self._version_tuple

    @property
    def version_spec(self):
        if self._version_spec is None:
            self._version_spec = Version(self.version)
        return self._version_spec


class PythonOrgSearch(Prefab):
    release_page: str = RELEASE_PAGE
    release_file_page: str = RELEASE_FILE_PAGE

    release_page_cache: str | None = None
    release_file_page_cache: str | None = None

    _releases: list[PythonRelease] | None = attribute(default=None, private=True)
    _release_files: list[PythonReleaseFile] | None = attribute(default=None, private=True)

    @property
    def releases(self) -> list[PythonRelease]:
        if self._releases is None:
            if self.release_page_cache:
                data = json.loads(self.release_page_cache)
            else:
                with urlopen(self.release_page) as req:
                    data = json.load(req)

            self._releases = [PythonRelease.from_dict(release) for release in data]
            self._releases.sort(key=lambda ver: ver.version_tuple, reverse=True)

        return self._releases

    @property
    def release_files(self) -> list[PythonReleaseFile]:
        if self._release_files is None:
            if self.release_file_page_cache:
                data = json.loads(self.release_file_page_cache)
            else:
                with urlopen(self.release_file_page) as req:
                    data = json.load(req)

            self._release_files = [PythonReleaseFile.from_dict(relfile) for relfile in data]
        return self._release_files

    def matching_versions(self, specifier: SpecifierSet, prereleases=False) -> list[PythonRelease]:
        return [
            release
            for release in self.releases
            if specifier.contains(release.version_spec, prereleases=prereleases)
        ]

    def matching_downloads(
        self,
        specifier: SpecifierSet,
        prereleases: bool = False
    ) -> list[PythonDownload]:

        matching_downloads = []
        releases = self.matching_versions(specifier, prereleases)

        release_uri_map = {
            rel.resource_uri: rel
            for rel in releases
        }

        for release_file in self.release_files:
            if release_file.release in release_uri_map.keys():
                rel = release_uri_map[release_file.release]
                matching_downloads.append(
                    PythonDownload(
                        name=rel.name,
                        version=rel.version_str,
                        url=release_file.url,
                        md5_sum=release_file.md5_sum,
                    )
                )

        matching_downloads.sort(key=lambda dl: dl.version_spec, reverse=True)
        return matching_downloads

    def all_matching_binaries(self, specifier: SpecifierSet, prereleases=False) -> list[PythonDownload]:
        tags = get_binary_tags()
        latest_binaries = []

        for download in self.matching_downloads(specifier, prereleases):
            for tag in tags:
                if download.url.endswith(tag):
                    latest_binaries.append(download)

        return latest_binaries

    def latest_minor_binaries(self, specifier: SpecifierSet, prereleases=False) -> list[PythonDownload]:
        tags = get_binary_tags()
        latest_binaries = []
        versions_included = set()

        for download in self.matching_downloads(specifier, prereleases):
            if download.version_tuple[:2] in versions_included:
                continue

            for tag in tags:
                if download.url.endswith(tag):
                    versions_included.add(download.version_tuple[:2])
                    latest_binaries.append(download)

        return latest_binaries

    def latest_binary_match(self, specifier: SpecifierSet, prereleases=False) -> PythonDownload:
        tags = get_binary_tags()
        for download in self.matching_downloads(specifier, prereleases):
            for tag in tags:
                if download.url.endswith(tag):
                    return download
