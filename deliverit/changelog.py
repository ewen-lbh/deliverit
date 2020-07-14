"""
Functions related to changelogs
"""

from deliverit.context import Context
from deliverit.version import Version
from pathlib import Path
from typing import *

from chachacha.drivers.kac import ChangelogFormat

from deliverit.ui import *


def get_release_notes_for_version(version: Version, changelog_contents: str) -> str:
    in_current_version = False
    release_notes_lines = []
    for line in changelog_contents.splitlines():
        if line.startswith("##"):
            line = line.rstrip("# ").strip("[]")
            if line.split(" - ")[0] == str(version):
                in_current_version = True
            elif in_current_version:
                release_notes_lines += [line]
            else:
                in_current_version = False
    return "\n".join(release_notes_lines)


def update(ctx: Context, changelog_path: str, tag_template: str):
    changelog = ChangelogFormat(changelog_path)
    if not Path(changelog_path).is_file():
        changelog.init()
    changelog_config = changelog.get_config(init=True)
    changelog_config.git_provider = "GH"
    changelog_config.repo_name = ctx.repository_full_name
    changelog_config.tag_template = tag_template
    changelog.write(config=changelog_config)
    try:
        changelog.release(ctx.version_bump)
    except SystemExit:
        print_on_same_line(
            red("Please add changes to the ")
            + b("Unreleased")
            + red(" section in ")
            + b(changelog_path)
        )
        exit(1)
