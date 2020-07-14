"""
Functions related to version operations
"""
from typing import *
import subprocess
from subprocess import CalledProcessError
from parse import parse

from deliverit.ui import *

class Version:
    def __init__(self, major: int, minor: int, patch: int) -> None:
        self.major, self.minor, self.patch = major, minor, patch

    @classmethod
    def parse(cls, version_str: str) -> 'Version':
        """
        Returns a 'Version' instance from a "X.Y.Z" string
        """
        return cls(*map(int, version_str.split('.')))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def bump(self, bump: str) -> 'Version':
        """
        Returns a bumped version of itself bumped
        by a `bump` bump (can be "major", "minor" or "patch")
        """
        if bump == "major":
            return Version(self.major+1, self.minor, self.patch)
        if bump == "minor":
            return Version(self.major, self.minor+1, self.patch)
        if bump == "patch":
            return Version(self.major, self.minor, self.patch+1)

        raise ValueError("bump must be one of 'major', 'minor' or 'patch'")
        
def get_current_version_from_git_tag(
    tag_template: str, fallback_version: Version
) -> Optional[Version]:
    """
    Uses git to determine the current version.
    Primarily used when language=go
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--abbrev=0"], capture_output=True, check=True
        )
        stdout = result.stdout.decode("utf-8")
        stderr = result.stderr.decode("utf-8")
    except CalledProcessError:
        print(red("Could not get the current version from git tags"))
        return fallback_version
    if stderr.startswith("fatal: No names found"):
        print(
            warn(
                "No git tags found, can't determine current version. "
                f"Assuming a initial version of v{em(fallback_version)}"
            )
        )
        return fallback_version
    else:
        return Version.parse(parse(tag_template, stdout).named["new"])
