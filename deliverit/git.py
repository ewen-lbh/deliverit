"""
Functions related to git
"""

from __future__ import annotations
from typing import Union, Optional, Any
import subprocess


def get_latest_commit_hash() -> str:
    """
    Gets the latest commit hash by running
    git log --format=%H -n 1
    """
    latest_commit_hash = (
        subprocess.run(
            ["git", "log", "--format=%H", "-n", "1"], capture_output=True, check=True
        )
        .stdout.decode("utf-8")
        .replace("\n", "")
    )
    return latest_commit_hash


def has_git_remote() -> bool:
    """
    Checks if a repository has at least one remote set up.
    Relies on the emptyness of the stdout of `git remote`.
    Returns `False` if the return code is non-zero
    """
    # pylint: disable=subprocess-run-check
    result = subprocess.run(["git", "remote"], capture_output=True)
    return result.returncode == 0 and result.stdout != b""
