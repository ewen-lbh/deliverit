"""
Extracts required info from various manifest file formats
"""
import re
from typing import *
from pathlib import Path
import json
import configparser

import toml
from recordclass import RecordClass

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


class PyProjectTOML(ManifestInfoExtractor):
    def _parse(self, fileobj: "IO[Any]", filepath: str):
        self.parsed = toml.load(fileobj)
        self.metadata = self.parsed["tool"]["poetry"]

    @property
    def old_version(self) -> Version:
        return Version.parse(self.metadata["version"])

    @property
    def package_name(self) -> str:
        return self.metadata["name"].replace("-", "_")

    @property
    def repository_url(self) -> Optional[str]:
        return self.metadata.get("repository")


class PackageJSON(ManifestInfoExtractor):
    def _parse(self, fileobj: "IO[Any]", filepath: str):
        self.parsed: dict = json.load(fileobj)

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
        if type(repo) is dict:
            url = repo.get("url")
        else:
            url = repo

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


class SetupCFG(ManifestInfoExtractor):
    def _parse(self, fileobj: "IO[Any]", filepath: str):
        self.parsed = configparser.ConfigParser()
        self.parsed.read_file(fileobj)

    def _read_value(self, value: str) -> str:
        """Seems like values in setup.cfg can be pointers to files, handle that."""
        if value.startswith("file:"):
            filepath = value.replace("file:", "").strip()
            return Path(filepath).read_text("utf-8")
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


class ManifestInfo(RecordClass):
    old_version: Optional[Version]
    package_name: Optional[str]
    repository_url: Optional[str]


def load(filepath: str) -> Tuple[Optional[Version], Optional[str], Optional[str]]:
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
