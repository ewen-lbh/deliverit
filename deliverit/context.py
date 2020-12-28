from __future__ import annotations
from typing import Union, Optional, Any
from os.path import expandvars
import time
from math import floor
from termcolor import cprint

from pydantic import BaseModel

from deliverit.version import Version


class Context(BaseModel):
    package_name: Optional[str] = None
    repository_url: Optional[str] = None
    repository_full_name: Optional[str] = None
    repository_name: Optional[str] = None
    repository_owner: Optional[str] = None
    new_version: Optional[Version] = None
    old_version: Optional[Version] = None
    version_bump: Optional[str] = None
    debugging: bool = False

    def debug(self, message: str):
        if self.debugging:
            timestamp = str(time.time() - floor(time.time())).replace("0.", ".")
            cprint(f"[[{timestamp:0<18}]] {message}", attrs=("dark",))

    def apply(self, format_str: Optional[str], env_aware: bool = True) -> str:
        """
        Replaces placeholders in format_str
        """
        if format_str is None:
            return ""
        applied = format_str.format(
            package=self.package_name,
            repo_url=self.repository_url,
            repo_full=self.repository_full_name,
            repo=self.repository_name,
            owner=self.repository_owner,
            new=self.new_version,
            old=self.old_version,
            bump=self.version_bump,
        )
        if not env_aware:
            self.debug(f"ctx.apply[] {format_str!r}~>{applied!r}")
            return applied

        applied = expandvars(applied)
        self.debug(f"ctx.apply[env_aware] {format_str!r}~>{applied!r}")
        return applied
