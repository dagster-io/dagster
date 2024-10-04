import os
from collections import defaultdict
from pathlib import Path
from typing import Iterator, List, Mapping, NamedTuple, Optional, Sequence

import click
import git

GITHUB_URL = "https://github.com/dagster-io"
OSS_ROOT = Path(__file__).parent.parent
OSS_REPO = git.Repo(OSS_ROOT)
CHANGELOG_PATH = OSS_ROOT / "CHANGES.md"
INTERNAL_REPO = git.Repo(os.environ["DAGSTER_INTERNAL_GIT_REPO_DIR"])
INTERNAL_DEFAULT_STR = "If a changelog entry is required"

CHANGELOG_HEADER = "## Changelog"
IGNORE_TOKEN = "NOCHANGELOG"

CATEGORIES = {
    "NEW": "New",
    "BUGFIX": "Bugfixes",
    "DOCS": "Documentation",
    "BREAKING": "Breaking Changes",
    "DEPRECATE": "Deprecations",
    "Plus": "Dagster Plus",
    None: "Invalid",
}


class ParsedCommit(NamedTuple):
    issue_link: str
    changelog_category: str
    raw_changelog_entry: Optional[str]
    raw_title: str
    author: str
    repo_name: str
    ignore: bool

    @property
    def documented(self) -> bool:
        return bool(self.raw_changelog_entry)


def _get_previous_version(new_version: str) -> str:
    split = new_version.split(".")
    previous_patch = int(split[-1]) - 1
    assert previous_patch >= 0, "Must explicitly set `previous_version` on major releases."
    return ".".join([*split[:-1], str(previous_patch)])


def _get_libraries_version(new_version: str) -> str:
    split = new_version.split(".")
    new_minor = int(split[1]) + 16
    return ".".join(["0", str(new_minor), split[2]])


def _get_parsed_commit(commit: git.Commit) -> ParsedCommit:
    """Extracts a set of useful information from the raw commit message."""
    title = str(commit.message).splitlines()[0]
    # me avoiding regex -- titles are formatted as "Lorem ipsum ... (#12345)" so we can just search
    # for the last octothorpe and chop off the closing paren
    repo_name = str(commit.repo.git_dir).split("/")[-2]
    issue_number = title.split("#")[-1][:-1]
    issue_link = f"[#{issue_number}]({GITHUB_URL}/{repo_name}/pull/{issue_number})"

    # find the first line that has `CHANGELOG` in the first few characters, then take the next
    # non-empty line
    found_start = False
    found_end = False
    ignore = False
    changelog_category = None
    raw_changelog_entry = ""
    for line in str(commit.message).split("\n"):
        if found_start and line.strip():
            if line.startswith(IGNORE_TOKEN):
                ignore = True
                break
            if INTERNAL_DEFAULT_STR in line:
                # ignore changelog entry if it has not been updated
                raw_changelog_entry = ""
                break
            if line.lower().startswith("- ["):
                found_end = True
            if not found_end:
                raw_changelog_entry += " " + line.strip()
        if found_end:
            if line.lower().startswith("- [x]"):
                bt1 = line.find("`")
                changelog_category = line[bt1 + 1 : line.find("`", bt1 + 1)]
                break
        if line.startswith(CHANGELOG_HEADER):
            found_start = True

    return ParsedCommit(
        issue_link=issue_link,
        changelog_category=CATEGORIES.get(changelog_category, "Invalid"),
        raw_changelog_entry=raw_changelog_entry,
        raw_title=title,
        author=str(commit.author.name),
        repo_name=repo_name,
        ignore=ignore,
    )


def _get_documented_section(documented: Sequence[ParsedCommit]) -> str:
    grouped_commits: Mapping[str, List[ParsedCommit]] = defaultdict(list)
    for commit in documented:
        grouped_commits[commit.changelog_category].append(commit)

    documented_text = ""
    for category in CATEGORIES.values():
        documented_text += f"\n\n### {category}\n"
        for commit in grouped_commits.get(category, []):
            documented_text += f"\n* {commit.raw_changelog_entry} {commit.issue_link}"
    return documented_text


def _get_undocumented_section(undocumented: Sequence[ParsedCommit]) -> str:
    undocumented_text = "# Undocumented Changes"

    grouped_commits: Mapping[str, List[ParsedCommit]] = defaultdict(list)
    for commit in undocumented:
        grouped_commits[commit.author].append(commit)

    for author, commits in sorted(grouped_commits.items()):
        undocumented_text += f"\n- [ ] {author}"
        for commit in commits:
            undocumented_text += (
                f"\n\t- [ ] (repo:{commit.repo_name}) {commit.issue_link} {commit.raw_title}"
            )
    return undocumented_text


def _get_commits(
    repos: Sequence[git.Repo], new_version: str, prev_version: str
) -> Iterator[ParsedCommit]:
    for repo in repos:
        for commit in repo.iter_commits(rev=f"release-{prev_version}..release-{new_version}"):
            yield _get_parsed_commit(commit)


def _generate_changelog_text(new_version: str, prev_version: str) -> str:
    documented: List[ParsedCommit] = []
    undocumented: List[ParsedCommit] = []

    for commit in _get_commits([OSS_REPO, INTERNAL_REPO], new_version, prev_version):
        if commit.ignore:
            continue
        elif commit.documented:
            documented.append(commit)
        elif commit.repo_name != str(INTERNAL_REPO.git_dir).split("/")[-2]:
            # default to ignoring undocumented internal commits
            undocumented.append(commit)

    header = f"# Changelog \n\n## {new_version} (core) / {_get_libraries_version(new_version)} (libraries)"
    return f"{header}{_get_documented_section(documented)}\n\n{_get_undocumented_section(undocumented)}"


@click.command()
@click.argument("new_version", type=str, required=True)
@click.argument("prev_version", type=str, required=False)
def generate_changelog(new_version: str, prev_version: Optional[str] = None) -> None:
    if prev_version is None:
        prev_version = _get_previous_version(new_version)

    # ensure that the release branches are available locally
    for repo in [OSS_REPO, INTERNAL_REPO]:
        repo.git.checkout("master")
        repo.git.pull()
        repo.git.checkout(f"release-{prev_version}")
        repo.git.pull()
        repo.git.checkout(f"release-{new_version}")
        repo.git.pull()
        repo.git.checkout("master")

    new_text = _generate_changelog_text(new_version, prev_version)
    with open(CHANGELOG_PATH, "r") as f:
        current_changelog = f.read()

    new_changelog = new_text + current_changelog[1:]

    with open(CHANGELOG_PATH, "w") as f:
        f.write(new_changelog)


if __name__ == "__main__":
    generate_changelog()
