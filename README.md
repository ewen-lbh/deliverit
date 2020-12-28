# deliverit

Makes releasing versions a breeze.

_<sub>Jump to the <a href="#table-of-contents">table of contents</a></sub>_

## Installation

```shell
pip install deliverit
```

## Configuration

Create a `.deliverit.yaml` file in the root of your project.

Here are the configuration keys.

### `language`

Declare the project's programming language. Sets smart defaults for other configuration keys.

Allowed values:

- rust
- swift
- clojure
- perl
- r
- d
- elm
- go
- haskell
- haxe
- elixir
- erlang
- julia
- java
- javascript (or "js")
- typescript (or "ts")
- .net
- objective-c (or "obj-c")
- php
- dart
- python
- ruby
- crystal
- lua

Note that you do not need to set this value if your language does not appear here. This is purely used to set defaults.

### `package_name` , `repository_url` and `version`

Some languages and/or package managers have no manifest files, so sometimes information cannot be extracted by reading another file.

Sometimes your manifest file has no (standardized or not) way to specify some specific information (the repository URL most of the time)

If you're in this situation, or just want to override some information just for deliverit for some reason, set these.

Note that some manifest files have no keys directly related to repositories but instead generic ones like "project homepage" or "project url". For those, if `repository_url` is not set manually, it'll expect the repository URL to be declared in this field. If your package has its own separate website, set `repository_url` explicitly.

### `manifest_file`

Declare the manifest file from which to extract some information. Allowed values:

in all of these default values `{FOLDER}` is replaced with `.deliverit.yaml`'s parent folder name.
For those, it is **highly advised** to explicitly declare the manifest file by setting `manifest_file`

| Value                      | Is default value when `language` is set to: |
| -------------------------- | ------------------------------------------- |
| setup.cfg                  | python                                      |
| elm.json                   | elm                                         |
| haxelib.json               | haxe                                        |
| package.json               | js, ts                                      |
| composer.json              | php                                         |
| pom.xml                    | java                                        |
| META.json                  | perl                                        |
| META.yml                   | /                                           |
| Cargo.toml                 | rust                                        |
| Manifest.toml+Project.toml | julia                                       |
| pyproject.toml             | /                                           |
| pubspec.yaml               | dart                                        |
| shard.yml                  | crystal                                     |
| dub.json                   | d                                           |
| dub.sdl                    | /                                           |
| {FOLDER}.cabal             | haskell                                     |
| project.clj                | clojure                                     |
| package.js                 | /                                           |
| {FOLDER}.podspec           | objective-c                                 |
| Gemspec                    | ruby                                        |
| Package.swift              | swift                                       |
| mix.exs                    | elixir or erlang                            |

### `registry`

Declare to which site to publish the package to. Default values according to `manifest_file`'s values:

| `manifest_file` with value: | makes `registry` default to: |
| --------------------------- | ---------------------------- |
| setup.cfg                   | pypi.org                     |
| elm.json                    | package.elm-lang.org         |
| haxelib.json                | lib.haxe.org                 |
| package.json                | npmjs.com                    |
| composer.json               | packagist.org                |
| pom.xml                     | maven.org                    |
| META.json                   | cpan.org                     |
| META.yml                    | cpan.org                     |
| Cargo.toml                  | crates.io                    |
| Manifest.toml+Project.toml  | pkg.julia.org                |
| pyproject.toml              | pypi.org                     |
| pubspec.yaml                | pub.dartlang.org             |
| shard.yml                   | shards.info                  |
| dub.json                    | code.dlang.org               |
| dub.sdl                     | code.dlang.org               |
| {FOLDER}.cabal              | hackage.haskell.org          |
| project.clj                 | clojars.org                  |
| package.js                  | atmospherejs.com             |
| {FOLDER}.podspec            | cocoapods.org                |
| {FOLDER}.gemspec            | rubygems.org                 |
| Package.swift               | `null`                       |
| mix.exs                     | hex.pm                       |
| {FOLDER}.rockspec           | luarocks.org                 |

Now onto the fun stuff that actually makes sense to define and will directly impact what deliverit does.
Every configuration option, unless specified, has access to those placeholders that will be replaced with their respective values:

| The string    | Will be replaced with                                 |
| ------------- | ----------------------------------------------------- |
| `{package}`   | the package's name                                    |
| `{new}`       | the new (after bumping) version                       |
| `{old}`       | the old (before bumping) version                      |
| `{repo_full}` | the repository's full name, including the owner part. |
| `{repo_url}`  | the repository's full URL                             |
| `{repo}`      | the repository's name (without the "owner/" part)     |
| `{owner}`     | the repository's owner (user or organization)         |
| `{bump}`      | the version bump chosen ("major", "minor" or "patch") |

Note that we are using python's [`str.format`](https://docs.python.org/3.8/library/stdtypes.html#str.format), so [the format](https://pyformat.info/)'s special syntax is available and will work as expected.

### `commit_message`

The commit mesage containing all of the changes [search-and-replace modifications](#codemods), manifest file version bump, changelog changes, etc.

Default value: `Release {new}`

Example values:

- Gitmoji standard: `🔖 Release {new}`
- Semantic commits standard: `chore: release {new}`

### `tag_name`

The name of the git tag associated with the commit.

Default: `v{tag}`

Note: if `manifest_file` is `null` or if the version can't be extracted from it, deliverit will try to guess the version by parsing the latest tag using the format ([yes, you can do the inverse operation of `str.format`](https://pypi.org/project/parse))

### `milestone_title`

The name of the Github milestone deliverit will try to close after comitting and releasing the new version. If set to `null`, the [step](#steps) `close_milestone` is set to `off`

Default: `'{new}'`

### `release_title`

deliverit will use this to generate the Github release's title. If set to `null`, the [step](#steps) `create_release` is set to `off`

Default: `'{new}'`

### `changelog`

The path to the CHANGELOG.md file. Note: the changelog **must** follow the [keepachangelog standard](https://keepachangelog.com). I use [keepachangelog](https://pypi.org/project/keepachangelog) and [my fork of aogier/chachacha](https://github.com/ewen-lbh/chachacha) to parse and modify changelogs

### `release_assets`

Specifies the list of assets to upload to your Github release.

Each item is an object with the following keys:

#### `file`

The file name.

#### `label`

The file's associated label, which will appear on the UI

#### `create_with`

A command that will be executed before uploading the file to create it. If the commands returns an nonzero exit code or if the file is not found after running the command, deliverit prints a warning (this is not considered fatal as you can add those assets yourself to github release later)

Default value: `null`

#### `delete_after`

Whether to delete the file after uploading.

Default value: `false`

---

Default value for `release_assets`:

```yaml
release_assets:
    - file: source-{package}-{new}.tar.gz
      label: Source code for {new}
      create_with: tar -cvzf source-{package}-{new}.tar.gz
      delete_after: yes
```

### `codemods`

Perform manual regex-based search-and-replace operations in your code base. Useful for in-code version-dependant constants (like python's `__init__.__version__` convention) or when your package manager's manifest file is not supported yet. ([please do request it!](https://github.com/ewen-lbh/deliverit/issues/new?title=Add%20support%20for%20{your%20manifest%20file%20format}&body=Please%20add%20support%20for%20{package%20manager}%27s%20{manifest%20file%20format}))

This setting is a list of objects with the following properties:

#### `in`

specifies in which file(s) will the replacement be performed. Can be glob patterns. Can be a list of those too.

#### `search`

Will search for the following regex. Be sure to escape this correctly (see [this cheatsheet on YAML string literals](https://yaml-multiline.info))

#### `replace`

Will replace all of the occurences of `search` with this. Note that you _can_ use both placeholders (e.g. `{new}`) and regex capture groups references (e.g. `\1`) at the same time. If your replacement includes a literal `\`, escape it like so: `\\`

---

An example to illustrate, this will probably be the value of `codemods` for most python libraries:

```yaml
codemods:
    - in: ./{package}/__init__.py # the  "./" is not required, I used it to avoid having to quote the value
      search: ^__version__ = ".+"$
      replace: __version__ = "{new}"
```

### `steps`

This object is used to individually and switch on or off certain steps. Some steps can also take commands which will be executed for their corresponding step. Note that most of these are automatically disabled or enabled based on the other configuration keys.

For string values here, all of the preceding configuration values are available as placeholders, eg. `{changelog}` will be replaced with the `changelog` setting's value (with the setting value's placeholders applied)

Some additionnal placeholders are available as well:

Note that it is highly encouraged to quote those placeholders with `{placeholder!r}` if their values can contain spaces

| The placeholder            | will be replaced with                                                                                                                         |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `{codemod_affected_files}` | All files that were affected by `codemods`. Do not quote this one with `!r` as it contains a space-separated list of already-quoted filepaths |
| `{bump_commit_hash}`       | The hash of the commit produced by `git_commit`. Set to the empty string before the `git_commit` step is executed.                            |

Placeholders of config values can also be prefixed by `_` (e.g. `{_tag_name}`) to get their "non-computed" versions. (i.e. if `tag_name` is set to `v{new}` and `{new}` evaluates to `0.5.0`, `{tag_name}` will be replaced with `v0.5.0` while `{_tag_name}` will be replaced with `v{new}`)

Environment variables from `.env` are also available as regular: `echo $GITHUB_TOKEN` is handled as expected.

#### `update_changelog`

Whether to update the changelog file.

Default: `true` if `changelog` is not `null`

#### `do_codemods`

Whether to run code modifications.

Default: `true` if `codemods` is not empty

#### `bump_manifest_version`

Whether to bump the manifest file's declared version.

Default: `true` if `manifest_file` is not `null`

#### `git_add`

The command used for staging changes.

Default: `git add {changelog!r} {codemod_affected_files} {manifest_file!r}`

#### `git_commit`

The command used to commit staged changes.

Default: `git commit -m {commit_message!r}`

#### `git_tag`

The command used to create the tag.

Default: `git tag -a {tag_name!r} {bump_commit_hash} -m {commit_message!r}`

#### `git_push`

The command used to push changes to github.

Default: `git push`

#### `git_push_tag`

The command used to push the tag created by `git_tag`.

Default: `git push origin {tag_name!r}`

#### `build_for_registry`

The command used to build potential files required for publishing to the registry.

Default values according to `manifest_file`'s value:

| if `manifest_file` is set to: | `steps.build_for_registry` defaults to: |
| ----------------------------- | --------------------------------------- |
| setup.cfg                     | `python3 setup.py sdist bdist_wheel`
| elm.json                      | ``
| haxelib.json                  | ``
| package.json                  | `npm run build`
| composer.json                 | ``
| pom.xml                       | ``
| META.json                     | ``
| META.yml                      | ``
| Cargo.toml                    | ``
| Manifest.toml+Project.toml    | ``
| pyproject.toml                | `poetry build`
| pubspec.yaml                  | ``
| shard.yml                     | ``
| dub.json                      | ``
| dub.sdl                       | ``
| *.cabal                       | ``
| project.clj                   | ``
| package.js                    | ``
| *.podspec                     | ``
| *.gemspec                     | ``
| Package.swift                 | ``
| mix.exs                       | ``
| *.rockspec                    | ``

<sub>Most of these values still need to be research and are hence empty for now</sub>

#### `publish_to_registry`

The command used to publish the package to the registry.

Default values according to `manifest_file`'s value:

| if `manifest_file` is set to: | `steps.build_for_registry` defaults to: |
| ----------------------------- | --------------------------------------- |
| setup.cfg                     | `python3 -m twine upload --repository testpypi dist/*`
| elm.json                      | ``
| haxelib.json                  | ``
| package.json                  | `npm publish`
| composer.json                 | ``
| pom.xml                       | ``
| META.json                     | ``
| META.yml                      | ``
| Cargo.toml                    | ``
| Manifest.toml+Project.toml    | ``
| pyproject.toml                | `poetry publish`
| pubspec.yaml                  | ``
| shard.yml                     | ``
| dub.json                      | ``
| dub.sdl                       | ``
| *.cabal                       | ``
| project.clj                   | ``
| package.js                    | ``
| *.podspec                     | ``
| *.gemspec                     | ``
| Package.swift                 | ``
| mix.exs                       | ``
| *.rockspec                    | ``

<sub>Most of these values still need to be research and are hence empty for now</sub>

#### `create_github_release`

_You will need to have `GITHUB_TOKEN="your github personal access token here"` set for this step to work._

Default: `true` if `release_title` is not `null`

#### `add_assets_to_github_release`

_You will need to have `GITHUB_TOKEN="your github personal access token here"` set for this step to work._

Default: `true` if `release_assets` is not empty

#### `close_milestone`

_You will need to have `GITHUB_TOKEN="your github personal access token here"` set for this step to work._

Default `true` if `milestone_title` is not `null`

#### `custom_commands`

A list of objects containing the following values:

The commands will be run in the list's declared order.

##### `after`

Run the command after the step specified. If set to `everything`, runs the command at the end. If set to `nothing`, runs the command before anything.

The step specified cannot be `custom_commands`.

##### `run`

Run the command specified here. The same placeholders as the regular steps' string values are handled. (i.e. `{changelog}` works.)

## Table of contents

- [deliverit](#deliverit)
  - [Installation](#installation)
  - [Configuration](#configuration)
    - [`language`](#language)
    - [`package_name` , `repository_url` and `version`](#package_name--repository_url-and-version)
    - [`manifest_file`](#manifest_file)
    - [`registry`](#registry)
    - [`commit_message`](#commit_message)
    - [`tag_name`](#tag_name)
    - [`milestone_title`](#milestone_title)
    - [`release_title`](#release_title)
    - [`changelog`](#changelog)
    - [`release_assets`](#release_assets)
      - [`file`](#file)
      - [`label`](#label)
      - [`create_with`](#create_with)
      - [`delete_after`](#delete_after)
    - [`codemods`](#codemods)
      - [`in`](#in)
      - [`search`](#search)
      - [`replace`](#replace)
    - [`steps`](#steps)
      - [`update_changelog`](#update_changelog)
      - [`do_codemods`](#do_codemods)
      - [`bump_manifest_version`](#bump_manifest_version)
      - [`git_add`](#git_add)
      - [`git_commit`](#git_commit)
      - [`git_tag`](#git_tag)
      - [`git_push`](#git_push)
      - [`git_push_tag`](#git_push_tag)
      - [`build_for_registry`](#build_for_registry)
      - [`publish_to_registry`](#publish_to_registry)
      - [`create_github_release`](#create_github_release)
      - [`add_assets_to_github_release`](#add_assets_to_github_release)
      - [`close_milestone`](#close_milestone)
      - [`custom_commands`](#custom_commands)
        - [`after`](#after)
        - [`run`](#run)
  - [Table of contents](#table-of-contents)
