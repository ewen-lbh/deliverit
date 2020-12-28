"""Release new versions of your package with ease.

Usage:
    deliverit (major|minor|patch) [-y] [options] [--disable-step=STEP_ID...]

Options:
    -y --yes                   Don't ask for confirmation before each step
    --verbose                  Show more info
    --debug                    Show even more info
    --dry-run                  Don't actually run commands
    --config-file=FILEPATH     Path to the configuration file.
    -! --disable-step=STEP_ID  Disables the step with id STEP_ID. See Step IDs

Configuration file overrides:
    --language=TEXT            The package's programming language
    --package-name=TEXT        The package's name (useful is manifest-file is not set)
    --manifest-file=TEXT       The location of the file where some metadata is declared. Allowed: {pyproject.toml,setup.cfg,package.json}
    --repository-url=TEXT      The repository's URL (useful is manifest-file is not set)
    --registry=TEXT            The registry to which the package is published. Allowed values: {pypi.org,npmjs.com}
    --commit-message=TEXT      *The bump commit's message.
    --tag-name=TEXT            *The git tag's name.
    --milestone-title=TEXT     *The title of the milestone to close
    --release-title=TEXT       *The github release's title
    --changelog=FILE           The changelog file's location (must follow the Keep A Changelog standard)

Placeholders: (available to *-marked options)
    {new} is replaced with the new version.
    {old} is replaced with the old version.
    {bump} is replaced with the bump (minor, major or patch).
    {package} is the package's name.
    {repo} is the repository's name (WITHOUT the owner part)
    {owner} is the repository's owner name (or the organization's name).
    {repo_url} is the repository's full URL
"""
# TODO: custom commands
# TODO: rename version_declarations: to codemods:
# TODO: codemods.in: support glob patterns

from urllib.parse import urlparse
from deliverit.changelog import get_release_notes_for_version
from deliverit.version import Version, get_current_version_from_git_tag
from deliverit.git_remote import (
    close_milestone,
    create_github_release,
    is_hosted_on_github,
    split_repository_name,
    upload_assets_to_release,
)
from deliverit.git import get_latest_commit_hash
from os import getenv
from pathlib import Path
from subprocess import CalledProcessError
from __future__ import annotations
from typing import Union, Optional, Any

from docopt import docopt
from dotenv import load_dotenv
from github.MainClass import Github

from deliverit.context import Context
import deliverit
import deliverit.manifest_file
import deliverit.config
import deliverit.changelog
import deliverit.version_declaration
import deliverit.dotenv
from deliverit.git import has_git_remote
from deliverit.config import ConfigurationError
from deliverit.ui import *
from deliverit.step import make_step_function


def run():
    # Init some variables
    args = docopt(__doc__)
    ctx = Context()
    ctx.debugging = args["--debug"]

    # Check for dotenv file & load variables
    deliverit.dotenv.load(ctx)

    # read config file
    config_filepath = args["--config-file"] or (
        ".deliverit.yaml" if Path(".deliverit.yaml").is_file() else ".deliverit.yml"
    )

    config = deliverit.config.load(
        config_filepath, cli_args=args, has_git_remote=has_git_remote()
    )

    # Read manifest file to get some info
    # TODO: support multiple manifest files
    (
        ctx.old_version,
        ctx.package_name,
        ctx.repository_url,
    ) = deliverit.manifest_file.load(config.manifest_file)

    if ctx.old_version is None and config.tag_name is None:
        raise ConfigurationError("Please set either manifest_file or tag_name")
    ctx.old_version = ctx.old_version or get_current_version_from_git_tag(
        tag_template=config.tag_name, fallback_version=Version(0, 1, 0)
    )
    ctx.package_name = ctx.package_name or config.package_name
    if ctx.package_name is None:
        raise ConfigurationError(
            "Could not detect the package name. Set it explicitly with package_name"
        )
    ctx.repository_url = ctx.repository_url or config.repository_url
    if ctx.repository_url is None:
        raise ConfigurationError(
            "Could not detect the github repository's URL. Set it explicitly with repository_url"
        )

    # Check if repository is hosted on github
    if not is_hosted_on_github(ctx.repository_url):
        raise NotImplementedError("Your repository is not hosted on github")

    # Get the repository name
    ctx.repository_owner, ctx.repository_name = split_repository_name(
        ctx.repository_url
    )
    ctx.repository_full_name = f"{ctx.repository_owner}/{ctx.repository_name}"

    # Compute new version
    ctx.version_bump = (
        "major"
        if args["major"]
        else "minor"
        if args["minor"]
        else "patch"
        if args["patch"]
        else None
    )
    if ctx.version_bump is None:
        raise ValueError("No version bump specified.")
    ctx.new_version = ctx.old_version.bump(ctx.version_bump)

    # Compute some configurable values
    version_tag = config.tag_name.format(new=ctx.new_version)

    # Log info
    print(
        f"""\
Releasing a new {em(ctx.version_bump)} version!

     Upgrading package {em(ctx.package_name)} by {em(ctx.repository_owner)}
             hosted at {em(ctx.repository_url)}
          published on {em(config.registry)}
          from version {em(ctx.old_version)}
            to version {em(ctx.new_version)}
"""
    )

    # Make the step function
    step = make_step_function(args, config)

    # Modify the changelog
    step(
        "update_changelog",
        "Update the changelog",
        lambda: deliverit.changelog.update(
            ctx, ctx.apply(config.changelog), config.tag_name.replace("{new}", "{t}"),
        ),
    )

    # Codemods
    for declaration in config.version_declarations:
        new_content = ctx.apply(declaration.replace)
        step(
            "update_code_version",
            f"Replace {declaration.search} with {new_content} in {ctx.apply(declaration.in_)}",
            lambda: deliverit.version_declaration.update(ctx, declaration),
        )

    # Bump version
    step(
        "bump_manifest_version",
        "Bump the poetry version",
        command=ctx.apply(config.steps.bump_manifest_version),
    )

    # Add all changes
    step(
        "git_add",
        "Add changes",
        command=(
            "git",
            "add",
            *[ctx.apply(f.in_) for f in config.version_declarations],
            config.changelog,
            config.manifest_file,
        ),
    )

    # Commit
    step(
        "git_commit",
        "Commit the version bump",
        command=("git", "commit", "-m", ctx.apply(config.commit_message)),
    )

    # Add tag to commit
    try:
        latest_commit_hash = get_latest_commit_hash()
    except CalledProcessError:
        print(red("Could not get the latest commit's hash"))
        exit(1)
    step(
        "git_tag",
        f"Add tag {version_tag} to commit {latest_commit_hash[:7]}",
        command=(
            "git",
            "tag",
            "-a",
            version_tag,
            latest_commit_hash,
            "-m",
            ctx.apply(config.commit_message),
        ),
    )

    # Push
    step("git_push", "Push changes", command=("git", "push"))

    # Push tags
    step(
        "git_push_tag",
        f"Push the tag {version_tag}",
        command=("git", "push", "origin", version_tag),
    )

    # Build
    step(
        "build_for_registry",
        "Build for registry",
        command=config.steps.build_for_registry,
    )

    # Publish
    step(
        "publish_to_registry",
        f"Publish to {config.registry}",
        command=config.steps.publish_to_registry,
    )

    # Start a Github API session
    gh = Github(getenv("GITHUB_TOKEN"))

    # Get the release notes
    release_notes = get_release_notes_for_version(
        ctx.new_version, Path(config.changelog).read_text("utf-8")
    )

    release = step(
        "create_github_release",
        "Create a GitHub release",
        lambda: create_github_release(
            ctx,
            gh,
            ctx.apply(config.tag_name),
            ctx.apply(config.release_title),
            message=release_notes,
        ),
    )

    step(
        "add_assets_to_github_release",
        "Upload assets to the Github release",
        lambda: upload_assets_to_release(ctx, release, assets=config.release_assets,),
    )

    step(
        "close_milestone",
        "Close the milestone",
        lambda: close_milestone(ctx, gh, ctx.apply(config.milestone_title)),
    )
