"""
Functions related to Github (and planned support for Gitlab, Bitbucket,...)
"""

from __future__ import annotations
from typing import Union, Optional, Any
from urllib.parse import urlparse

import github

import deliverit.config
from deliverit.context import Context
from deliverit.ui import *


def is_hosted_on_github(repository_url: str) -> bool:
    """
    Checks if the repository at repository_url is hosted on github.com
    """
    return urlparse(repository_url).netloc == "github.com"


def split_repository_name(repository_url: str) -> tuple[str, str]:
    """
    Splits "owner/repo" into owner and repo
    """
    repository_full_name = urlparse(repository_url).path[1:]  # remove initial slash
    parts = repository_full_name.split("/")
    if len(parts) != 2:
        raise ValueError(
            f"The repository full name {repository_full_name!r} could not be split into OWNER/REPO"
        )
    return tuple(parts)


def close_milestone(ctx: Context, gh: github.Github, title: str):
    repo = gh.get_repo(ctx.repository_full_name)
    for milestone in repo.get_milestones():
        if milestone.title == title:
            milestone.edit(state="closed", title=title)
            break
    else:
        print(warn(f"No milestone with title {title!r} found"))


def create_github_release(
    ctx: Context, gh: github.Github, tag_name: str, title: str, message: str,
) -> github.GitRelease.GitRelease:
    repo = gh.get_repo(ctx.repository_full_name)
    return repo.create_git_release(tag=tag_name, name=title, message=message)


def upload_assets_to_release(
    ctx: Context,
    release: github.GitRelease.GitRelease,
    assets: list[deliverit.config.ReleaseAsset],
):
    # TODO: handle delete_after: and create_with:
    for asset in assets:
        file = ctx.apply(asset.file)
        label = ctx.apply(asset.label)
        release.upload_asset(file, label=label)
