import os
import re
import sys
from collections import defaultdict
from typing import Iterator, List, Mapping, NamedTuple, Optional, Sequence

import click
import git
from path import Path

GITHUB_URL = "https://github.com/dagster-io/dagster"
OSS_REPO = git.Repo(Path(__file__).parent.parent)
INTERNAL_REPO = git.Repo(os.environ["DAGSTER_INTERNAL_GIT_REPO_DIR"])

CHANGELOG_HEADER_PATTERN = re.compile(r"## CHANGELOG.*\[\s*(.*?)\s*\]")
IGNORE_TOKEN = "NOCHANGELOG"

CATEGORIES = {
    "NEW": "New",
    "BUG": "Bugfixes",
    "DOCS": "Documentation",
    "BREAKING": "Breaking Changes",
    "DEPRECATE": "Deprecations",
    "PLUS": "Dagster Plus",
    None: "Invalid",
}


class ParsedCommit(NamedTuple):
    issue_link: str
    changelog_category: str
    raw_changelog_entry: Optional[str]
    raw_title: str
    author: str
    repo_name: str

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
    return ".".join([split[0], str(new_minor), split[2]])


def _get_parsed_commit(commit: git.Commit) -> ParsedCommit:
    """Extracts a set of useful information from the raw commit message."""
    title = str(commit.message).splitlines()[0]
    # me avoiding regex -- titles are formatted as "Lorem ipsum ... (#12345)" so we can just search
    # for the last octothorpe and chop off the closing paren
    issue_number = title.split("#")[-1][:-1]
    issue_link = f"[#{issue_number}]({GITHUB_URL}/pull/{issue_number})"

    # find the first line that has `CHANGELOG` in the first few characters, then take the next
    # non-empty line
    found = False
    changelog_category = "Invalid"
    raw_changelog_entry = None
    for line in str(commit.message).split():
        if found and line:
            raw_changelog_entry = line
            break
        # give a buffer to allow us to match formats such as "## Changelog"
        match = CHANGELOG_HEADER_PATTERN.match(line)
        if match:
            changelog_category = CATEGORIES.get(match.group(1), changelog_category)
            found = True

    return ParsedCommit(
        issue_link=issue_link,
        changelog_category=changelog_category,
        raw_changelog_entry=raw_changelog_entry,
        raw_title=title,
        author=str(commit.author.name),
        repo_name=str(commit.repo.git_dir).split("/")[-2],
    )


def _normalize(name: str) -> str:
    return name.replace(" ", "").lower()


def _is_external_commit(commit: git.Commit) -> bool:
    # not super accurate at the moment, we'll probably need to actually ping the Github API
    return bool(commit.co_authors) and any(
        _normalize(str(a.name)) != _normalize(str(commit.author.name)) for a in commit.co_authors
    )


def _get_documented_section(documented: Sequence[ParsedCommit]) -> str:
    grouped_commits: Mapping[str, List[ParsedCommit]] = defaultdict(list)
    for commit in documented:
        grouped_commits[commit.author].append(commit)

    documented_text = ""
    for category in CATEGORIES.values():
        documented_text += f"### {category}\n\n"
        for commit in grouped_commits.get(category, []):
            documented_text += f"\n* {commit.issue_link} {commit.raw_changelog_entry}"
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
            if IGNORE_TOKEN in str(commit.message):
                continue

            yield _get_parsed_commit(commit)


def _generate_changelog(new_version: str, prev_version: str) -> None:
    documented: List[ParsedCommit] = []
    undocumented: List[ParsedCommit] = []

    for commit in _get_commits([OSS_REPO, INTERNAL_REPO], new_version, prev_version):
        if commit.documented:
            documented.append(commit)
        else:
            undocumented.append(commit)

    header = f"# Changelog {new_version}\n\n## {new_version} (core) / {_get_libraries_version(new_version)} (libraries)\n\n"
    sys.stdout.write(
        f"{header}\n{_get_documented_section(documented)}\n{_get_undocumented_section(undocumented)}"
    )


@click.command()
@click.argument("new_version", type=str, required=True)
@click.argument("prev_version", type=str, required=False)
def generate_changelog(new_version: str, prev_version: Optional[str] = None) -> None:
    if prev_version is None:
        prev_version = _get_previous_version(new_version)
    _generate_changelog(new_version, prev_version)


if __name__ == "__main__":
    generate_changelog()
