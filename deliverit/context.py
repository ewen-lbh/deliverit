from typing import *

from recordclass import RecordClass

from deliverit.version import Version

class Context(RecordClass):
    package_name: Optional[str] = None
    repository_url: Optional[str] = None
    repository_full_name: Optional[str] = None
    repository_name: Optional[str] = None
    repository_owner: Optional[str] = None
    new_version: Optional[Version] = None
    old_version: Optional[Version] = None
    version_bump: Optional[str] = None

    def apply(self, format_str: Optional[str]) -> str:
        """
        Replaces placeholders in format_str
        """
        if format_str is None:
            return ""
        return format_str.format(
            package=self.package_name,
            repo_url=self.repository_url,
            repo_full=self.repository_full_name,
            repo=self.repository_name,
            owner=self.repository_owner,
            new=self.new_version,
            old=self.old_version,
            bump=self.version_bump,
        )
