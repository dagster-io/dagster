import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterator, List, Mapping, NamedTuple, Optional, Sequence

import click
import git

GITHUB_URL = "https://github.com/dagster-io/dagster"
OSS_REPO = git.Repo(Path(__file__).parent.parent)
INTERNAL_REPO = git.Repo(os.environ["DAGSTER_INTERNAL_GIT_REPO_DIR"])

CHANGELOG_HEADER = "## Changelog"
CHANGELOG_HEADER_PATTERN = re.compile(rf"{CHANGELOG_HEADER}.*\[\s*(.*?)\s*\]")
IGNORE_TOKEN = "NOCHANGELOG"

CATEGORIES = {
    "New": "New",
    "Bug": "Bugfixes",
    "Docs": "Documentation",
    "Breaking": "Breaking Changes",
    "Deprecate": "Deprecations",
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
    raw_changelog_entry = ""
    for line in str(commit.message).split("\n"):
        if found and line.strip():
            raw_changelog_entry += " " + line.strip()
            continue
        is_header = line.startswith(CHANGELOG_HEADER)
        if is_header:
            raw_category_match = CHANGELOG_HEADER_PATTERN.match(line)
            raw_category = raw_category_match.group(1) if raw_category_match else None
            changelog_category = CATEGORIES.get(raw_category, changelog_category)
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


def _get_documented_section(documented: Sequence[ParsedCommit]) -> str:
    grouped_commits: Mapping[str, List[ParsedCommit]] = defaultdict(list)
    for commit in documented:
        grouped_commits[commit.changelog_category].append(commit)

    documented_text = ""
    for category in CATEGORIES.values():
        documented_text += f"### {category}\n"
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
