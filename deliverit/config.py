from typing import *
from keyword import iskeyword
from pathlib import Path

import yaml
from recordclass import RecordClass

BASE_DEFAULTS = {
    "language": None,
    "package_name": None,  # used when manifest_file == None
    "manifest_file": None,
    "repository_url": None,
    "registry": None,
    "commit_message": "Release {new}",
    "tag_name": "v{new}",
    "milestone_title": None,
    "release_title": "{new}",
    "release_assets": [
        {
            "label": "{new} Tarball",
            "file": "{package}-{new}.tar.gz",
            "create_with": "tar -cvzf dist/{package}-{new}.tar.gz ./",
            "delete_after": True,
        }
    ],
    "changelog": "CHANGELOG.md",
    "version_declarations": [],
    "steps": {
        "update_changelog": True,
        "update_code_version": True,
        "bump_manifest_version": "",
        "git_add": True,
        "git_commit": True,
        "git_tag": True,
        "git_push": True,
        "git_push_tag": True,
        "build_for_registry": "",
        "publish_to_registry": "",
        "create_github_release": True,
        "add_assets_to_github_release": True,
        "close_milestone": True,
    },
}

LANGUAGE_BASED_DEFAULTS = {
    "javascript": {
        "manifest_file": "package.json",
        "registry": "npmjs.com",
        "steps": {
            "bump_manifest_version": "npm version {bump}",
            "publish_to_registry": "npm publish {package}-{new}.tar.gz",
        },
    },
    "python": {
        "manifest_file": "pyproject.toml",
        "registry": "pypi.org",
        "release_assets": [  # TODO: this should be in sth like MANIFEST_FILE_BASED_DEFAULTS for pyproject.toml
            {"label": "{new} Tarball", "file": "{package}-{new}.tar.gz",},
            {
                "label": "Python wheel for {new}",
                "file": "dist/{package}-{new}-py3-none-any.whl",
            },
        ],
        "version_declarations": [
            {
                "in": "{package}/__init__.py",
                "search": '^__version__ = "(.+)"$',
                "replace": '__version__ = "{new}"',
            }
        ],
    },
    "go": {
        "manifest_file": None,
        "package_name": None,
        "registry": None,
        "tag_name": "v{new}",  # Pretty much _required_ to follow this format
        "release_assets": BASE_DEFAULTS["release_assets"]
        + [
            {"label": "Compiled binary", "file": "{package}", "create with": "go build"}
        ],
    },
}


class Steps(RecordClass):
    update_changelog: Union[bool, str] = True
    update_code_version: Union[bool, str] = True
    bump_manifest_version: str = ""
    git_add: bool = True
    git_commit: bool = True
    git_tag: bool = True
    git_push: bool = True
    git_push_tag: bool = True
    build_for_registry: str = ""
    publish_to_registry: str = ""
    create_github_release: Union[bool, str] = True
    add_assets_to_github_release: Union[bool, str] = True
    close_milestone: Union[bool, str] = True


class VersionDeclaration(RecordClass):
    in_: str
    search: str
    replace: str


class ReleaseAsset(RecordClass):
    file: str = "{package}-{new}.tar.gz"
    label: Optional[str] = None
    create_with: Optional[str] = None
    delete_after: Optional[str] = None


class Configuration(RecordClass):
    language: Optional[str]
    package_name: Optional[str]
    manifest_file: Optional[str]
    repository_url: Optional[str]
    registry: Optional[str]
    commit_message: Optional[str]
    tag_name: Optional[str]
    milestone_title: Optional[str]
    release_title: Optional[str]
    release_assets: List[ReleaseAsset]
    changelog: Optional[str]
    version_declarations: List[VersionDeclaration]
    steps: Steps


def resolve_defaults_steps(
    config: Dict[str, Any], has_git_remote: bool
) -> Dict[str, Union[bool, str]]:
    default_steps: Dict[str, Union[bool, str]] = {
        "update_changelog": False,
        "update_code_version": False,
        "bump_manifest_version": False,
        "git_add": False,
        "git_commit": False,
        "git_tag": False,
        "git_push": False,
        "git_push_tag": False,
        "build_for_registry": False,
        "create_github_release": False,
        "add_assets_to_github_release": False,
        "close_milestone": False,
    }
    ## update_changelog
    if config["changelog"]:
        default_steps["update_changelog"] = True
    ## update_code_version
    if config["version_declarations"]:
        default_steps["update_code_version"] = True
    ## bump_manifest_version
    if config["manifest_file"]:
        default_steps["bump_manifest_version"] = True
    ## git_add
    if True:
        default_steps["git_add"] = True
    ## git_commit
    if config["commit_message"]:
        default_steps["git_commit"] = True
    ## git_tag
    if config["tag_name"]:
        default_steps["git_tag"] = True
    ## git_push
    if has_git_remote:
        default_steps["git_push"] = True
    ## git_push_tag
    if default_steps.get("git_push") and default_steps.get("git_tag"):
        default_steps["git_push_tag"] = True
    ## build_for_registry
    if config["registry"]:
        default_steps["build_for_registry"] = True
    ## create_github_release
    if config["release_title"]:
        default_steps["create_github_release"] = True
    ## add_assets_to_github_release
    if config["release_assets"] and config["release_title"]:
        default_steps["add_assets_to_github_release"] = True
    ## close_milestone
    if config["milestone_title"]:
        default_steps["close_milestone"] = True
    return default_steps


def sanitize_keys(o: Dict[str, Any]) -> Dict[str, Any]:
    sanitized_dict: Dict[str, Any] = {}
    for key, value in o.items():
        key = key.replace(" ", "_")
        if iskeyword(key):
            key = f"{key}_"
        if type(value) is dict:
            value = sanitize_keys(value)
        if type(value) is list:
            value = [sanitize_keys(v) if type(v) is dict else v for v in value]
        sanitized_dict[key] = value
    return sanitized_dict


def apply_defaults(user_config: Dict[str, Any], has_git_remote: bool) -> Dict[str, Any]:
    config = {
        **BASE_DEFAULTS,
        **LANGUAGE_BASED_DEFAULTS[user_config["language"]],
        **user_config,
    }
    steps = {
        **resolve_defaults_steps(config, has_git_remote),
        **user_config.get("steps", {}),
    }

    config = {**config, **{"steps": steps}}
    return config


def _to_recordclasses(config: Dict[str, Any]) -> Configuration:
    config["release_assets"] = [ReleaseAsset(**i) for i in config["release_assets"]]
    config["steps"] = Steps(**config["steps"])
    config["version_declarations"] = [
        VersionDeclaration(**i) for i in config["version_declarations"]
    ]
    return Configuration(**config)


def override_with_cli_args(
    config: Dict[str, Any], cli_args: Dict[str, Any]
) -> Dict[str, Any]:
    for key, value in cli_args.items():
        config_key = key.replace("--", "").replace("-", "_")
        if config_key in BASE_DEFAULTS.keys() and value is not None:
            config = {
                **config,
                **yaml.load(f"{config_key}: {value}", Loader=yaml.SafeLoader),
            }
    return config


def load(
    filepath: str, cli_args: Dict[str, Any], has_git_remote: bool
) -> Configuration:
    if not Path(filepath).exists():
        return _to_recordclasses(resolve_defaults_steps(BASE_DEFAULTS, has_git_remote))

    config = Path(filepath).read_text(encoding="utf-8")
    config = yaml.load(config, Loader=yaml.SafeLoader)
    config = sanitize_keys(config)
    config = apply_defaults(config, has_git_remote)
    config = override_with_cli_args(config, cli_args)
    return _to_recordclasses(config)


class ConfigurationError(Exception):
    """Error with configuration (.deliverit.yaml files)"""
