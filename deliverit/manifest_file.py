"""
Extracts required info from various manifest file formats
"""
from __future__ import annotations

import configparser
import json
import re
from pathlib import Path
from typing import Any, Optional, Union

import toml
import xmltodict
import yaml
from pydantic import BaseModel

from deliverit.version import Version


class ManifestInfoExtractor:
    def __init__(self, fileobj: "IO[Any]", filepath: str) -> None:
        self._parse(fileobj, filepath)

    def _parse(self, fileobj: "IO[Any]", filepath: str):
        """Parse the file into a dict and sets self.parsed"""
        raise NotImplementedError("Please implement this method")

    @property
    def old_version(self) -> Version:
        """The old (current) version in a tuple of ints (major, minor, patch)"""
        raise NotImplementedError("Please implement this method")

    @property
    def package_name(self) -> str:
        """The package's (project) name"""
        raise NotImplementedError("Please implement this method")

    @property
    def repository_url(self) -> Optional[str]:
        """To which URL is the project's repository hosted?"""
        raise NotImplementedError("Please implement this method")

class TOMLManifestInfoExtractor(ManifestInfoExtractor):
    def _parse(self, fileobj: "IO[Any]", filepath: str):
        self.parsed = toml.load(fileobj)

class JSONManifestInfoExtractor(ManifestInfoExtractor):
    def _parse(self, fileobj: "IO[Any]", filepath: str):
        self.parsed = json.load(fileobj)

class YAMLManifestInfoExtractor(ManifestInfoExtractor):
    def _parse(self, fileobj: "IO[Any]", filepath: str):
        self.parsed = yaml.load(fileobj.read().decode("utf-8"), Loader=yaml.SafeLoader)

class XMLManifestInfoExtractor(ManifestInfoExtractor):
    def _parse(self, fileobj: "IO[Any]", filepath: str):
        self.parsed = xmltodict.parse(fileobj.read().decode("utf-8"))

class INIManifestInfoExtractor(ManifestInfoExtractor):
    def _parse(self, fileobj: "IO[Any]", filepath: str):
        self.parsed = configparser.ConfigParser()
        self.parsed.read_file(fileobj)

class PyProjectTOML(TOMLManifestInfoExtractor):
    @property
    def old_version(self) -> Version:
        return Version.parse(self.parsed["tool"]["poetry"]["version"])

    @property
    def package_name(self) -> str:
        return self.parsed["tool"]["poetry"]["name"].replace("-", "_")

    @property
    def repository_url(self) -> Optional[str]:
        return self.parsed["tool"]["poetry"].get("repository")


class PackageJSON(JSONManifestInfoExtractor):
    @property
    def old_version(self) -> Version:
        return Version.parse(self.parsed["version"])

    @property
    def package_name(self) -> str:
        return self.parsed["name"]

    @property
    def repository_url(self) -> Optional[str]:
        repo = self.parsed.get("repository")
        if repo is None:
            return None
        url = repo.get("url") if type(repo) is dict else repo
        if url is None:
            return None

        # owner/repo
        if re.match(r"([^/ ])+/([^/ ])+", url):
            return f"https://github.com/{url}"
        if re.match(r"github:([^/ ])+/([^/ ])+", url):
            return f"https://github.com/{url.replace('github:','')}"
        if re.match(r"gitlab:([^/ ])+/([^/ ])+", url):
            return f"https://github.com/{url.replace('gitlab:','')}"
        if re.match(r"bitbucket:([^/ ])+/([^/ ])+", url):
            return f"https://github.com/{url.replace('bitbucket:','')}"

        return None


class SetupCFG(INIManifestInfoExtractor):
    def _read_value(self, value: str) -> str:
        """Seems like values in setup.cfg can be pointers to files, handle that."""
        if value.startswith("file:"):
            filepath = value.replace("file:", "").strip()
            return Path(filepath).read_text("utf-8")
        elif value.startswith("attr:"):
            # TODO
            raise NotImplementedError(f"While parsing setup.cfg: could not resolve {value!r}: attr:-values are not supported yet")
        else:
            return value

    @property
    def old_version(self) -> Version:
        return Version.parse(self._read_value(self.parsed["metadata"].get("version")))

    @property
    def package_name(self) -> str:
        return self._read_value(self.parsed["metadata"].get("name"))

    @property
    def repository_url(self) -> Optional[str]:
        return self._read_value(self.parsed["metadata"].get("home-page"))


FILENAMES_TO_EXTRACTORS = {
    "pyproject.toml": PyProjectTOML,
    "package.json": PackageJSON,
    # "setup.py": SetupPY, AttributeError: module 'distutils' has no attribute 'core'
    "setup.cfg": SetupCFG,
}


class ManifestInfo(BaseModel):
    old_version: Optional[Version]
    package_name: Optional[str]
    repository_url: Optional[str]


def load(filepath: str) -> tuple[Optional[Version], Optional[str], Optional[str]]:
    """
    Loads the manifest file using the correct extractor and returns a tuple of:
    (old_version, package_name, repository_url)
    """
    try:
        extractor = FILENAMES_TO_EXTRACTORS[Path(filepath).name]
    except KeyError:
        raise ValueError(f"Unsupported manifest {Path(filepath).name!r}")

    manifest = extractor(open(filepath), filepath)
    return manifest.old_version, manifest.package_name, manifest.repository_url
