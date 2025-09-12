import os
import re
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from time import sleep
from typing import NamedTuple, Optional

import click
import git
import requests

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
    "DG": "dg & Components (Preview)",
    None: "Invalid",
}


class ParsedCommit(NamedTuple):
    issue_link: str
    changelog_category: str
    raw_changelog_entry: Optional[str]
    raw_title: str
    author: str
    author_email: str
    repo_name: str
    ignore: bool

    @property
    def documented(self) -> bool:
        return bool(self.raw_changelog_entry)


def _fetch_github_username_from_pr(pr_url: str) -> Optional[str]:
    """Fetch GitHub username from PR using GitHub API."""
    try:
        # Parse PR URL to extract owner, repo, and PR number
        # Expected format: https://github.com/owner/repo/pull/123
        url_parts = pr_url.split("/")
        if len(url_parts) >= 6 and "github.com" in pr_url:
            owner = url_parts[-4]  # dagster-io
            repo = url_parts[-3]  # dagster
            pr_number = url_parts[-1]  # 123

            # Use GitHub API to get PR info
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

            # Add a small delay to be respectful to GitHub API
            sleep(0.1)

            response = requests.get(api_url, timeout=10)
            response.raise_for_status()

            pr_data = response.json()
            username = pr_data.get("user", {}).get("login")

            if username and 3 <= len(username) <= 39:
                return username

    except Exception:
        # Silently fail - we'll fall back to "could not parse"
        pass

    return None


def _extract_github_username(commit: ParsedCommit) -> Optional[str]:
    """Extract GitHub username from commit author email, name, or PR webpage."""
    # Check if email is a GitHub noreply email
    if "@users.noreply.github.com" in commit.author_email:
        email_part = commit.author_email.split("@")[0]

        # Handle numeric format (12345+username@users.noreply.github.com)
        if "+" in email_part:
            return email_part.split("+")[1]  # "username"

        # Handle simple format (username@users.noreply.github.com)
        return email_part

    # Use author name as GitHub username if it looks like a reasonable username
    # (no spaces, reasonable length)
    author_name = commit.author
    if " " not in author_name and 3 <= len(author_name) <= 39:  # GitHub username limits
        return author_name

    # Last resort: try to fetch from the PR webpage
    if commit.issue_link and "github.com" in commit.issue_link:
        # Extract the URL from the markdown link [#123](https://github.com/...)
        url_match = re.search(r"\(([^)]+)\)", commit.issue_link)
        if url_match:
            pr_url = url_match.group(1)
            username = _fetch_github_username_from_pr(pr_url)
            if username:
                return username

    return None


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
    raw_changelog_entry_lines: list[str] = []
    has_testing_section = "## How I Tested These Changes" in str(commit.message)

    for line in str(commit.message).split("\n"):
        if found_start and line.strip():
            if line.startswith(IGNORE_TOKEN):
                ignore = True
                break
            if INTERNAL_DEFAULT_STR in line:
                # ignore changelog entry if it has not been updated
                raw_changelog_entry_lines = []
                break
            if line.lower().startswith("- ["):
                found_end = True
            if not found_end:
                raw_changelog_entry_lines.append(line.strip())
        if found_end:
            if line.lower().startswith("- [x]"):
                bt1 = line.find("`")
                changelog_category = line[bt1 + 1 : line.find("`", bt1 + 1)]
                break
        if line.startswith(CHANGELOG_HEADER):
            found_start = True

    # If there's a "How I Tested These Changes" section but no changelog content, ignore this commit
    if has_testing_section and not raw_changelog_entry_lines:
        ignore = True

    raw_changelog_entry = " ".join(raw_changelog_entry_lines)

    # If changelog entry contains the placeholder text, ignore this commit
    if "Insert changelog entry or delete this section" in raw_changelog_entry:
        ignore = True

    return ParsedCommit(
        issue_link=issue_link,
        changelog_category=CATEGORIES.get(changelog_category, "Invalid"),
        raw_changelog_entry=raw_changelog_entry,
        raw_title=title,
        author=str(commit.author.name),
        author_email=str(commit.author.email),
        repo_name=repo_name,
        ignore=ignore,
    )


def _get_documented_section(documented: Sequence[ParsedCommit]) -> str:
    grouped_commits: Mapping[str, list[ParsedCommit]] = defaultdict(list)
    for commit in documented:
        grouped_commits[commit.changelog_category].append(commit)

    documented_text = ""
    for category in CATEGORIES.values():
        category_commits = grouped_commits.get(category, [])
        if not category_commits:
            continue  # Skip empty categories

        documented_text += f"\n\n### {category}\n"
        for commit in category_commits:
            entry = commit.raw_changelog_entry or commit.raw_title

            # Put PR link on separate bullet point for easier deletion
            documented_text += f"\n- {entry}\n  - {commit.issue_link}"

            # Add GitHub profile link for the author if available
            github_username = _extract_github_username(commit)
            if github_username:
                documented_text += (
                    f"\n  - [@{github_username}](https://github.com/{github_username})"
                )
            else:
                documented_text += f"\n  - Could not parse user (author: {commit.author}, email: {commit.author_email})"
    return documented_text


def _get_commits(
    repos: Sequence[git.Repo], new_version: str, prev_version: str
) -> Iterator[ParsedCommit]:
    for repo in repos:
        for commit in repo.iter_commits(rev=f"release-{prev_version}..release-{new_version}"):
            yield _get_parsed_commit(commit)


def _generate_changelog_text(new_version: str, prev_version: str) -> str:
    documented: list[ParsedCommit] = []
    documented_internal: list[ParsedCommit] = []
    undocumented: list[ParsedCommit] = []

    internal_repo_name = str(INTERNAL_REPO.git_dir).split("/")[-2]

    for commit in _get_commits([OSS_REPO, INTERNAL_REPO], new_version, prev_version):
        if commit.ignore:
            continue
        elif commit.documented:
            if commit.repo_name == internal_repo_name:
                documented_internal.append(commit)
            else:
                documented.append(commit)
        elif commit.repo_name != internal_repo_name:
            # default to ignoring undocumented internal commits
            undocumented.append(commit)

    # Convert undocumented commits to Invalid category entries with <UNDOCUMENTED> placeholder
    for commit in undocumented:
        undocumented_commit = ParsedCommit(
            issue_link=commit.issue_link,
            changelog_category="Invalid",
            raw_changelog_entry="<UNDOCUMENTED>",
            raw_title=commit.raw_title,
            author=commit.author,
            author_email=commit.author_email,
            repo_name=commit.repo_name,
            ignore=False,
        )
        documented.append(undocumented_commit)

    header = f"# Changelog\n\n## {new_version} (core) / {_get_libraries_version(new_version)} (libraries)"

    sections = []

    # Main documented section (OSS repo + undocumented as Invalid)
    if documented:
        sections.append(_get_documented_section(documented))

    # Internal repo documented section
    if documented_internal:
        sections.append(
            f"\n\n## Internal Repository Changes\n{_get_documented_section(documented_internal)}"
        )

    return header + "".join(sections)


def _print_commit_info(commit: ParsedCommit, index: int, total: int) -> None:
    """Display commit information for interactive review."""
    print(f"\n{'=' * 80}")
    print(f"COMMIT {index}/{total}")
    print(f"{'=' * 80}")
    print(f"PR Link: {commit.issue_link}")
    print(f"Author: {commit.author} ({commit.author_email})")
    print(f"Commit Title: {commit.raw_title}")
    print(f"Current Category: {commit.changelog_category}")
    print(f"Current Entry: {commit.raw_changelog_entry or '<UNDOCUMENTED>'}")

    # Show GitHub username info
    github_username = _extract_github_username(commit)
    if github_username:
        print(f"GitHub Profile: @{github_username}")
    else:
        print("GitHub Profile: Could not parse")
    print("-" * 80)


def _get_user_action() -> str:
    """Get user's action choice for current commit."""
    while True:
        print("\nWhat would you like to do with this commit?")
        print("1) Accept as-is")
        print("2) Edit changelog entry")
        print("3) Ignore this commit (skip entirely)")
        print("q) Quit and save progress")

        choice = input("Enter choice (1/2/3/q): ").strip().lower()

        if choice in ["1", "accept", "a"]:
            return "accept"
        elif choice in ["2", "edit", "e"]:
            return "edit"
        elif choice in ["3", "ignore", "i"]:
            return "ignore"
        elif choice in ["q", "quit"]:
            return "quit"
        else:
            print("Invalid choice. Please enter 1, 2, 3, or q.")


def _get_edited_entry() -> str:
    """Get user's edited changelog entry."""
    print("\nEnter new changelog entry (or press Enter to keep current):")
    entry = input("> ").strip()
    return entry


def _get_category_choice() -> str:
    """Get user's category choice."""
    categories = [
        "New",
        "Bugfixes",
        "Documentation",
        "Dagster Plus",
        "Breaking Changes",
        "Deprecations",
    ]

    while True:
        print("\nSelect category:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}) {cat}")

        choice = input("Enter number: ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(categories):
                return categories[idx]
        except ValueError:
            pass

        print("Invalid choice. Please enter a number from the list.")


def _get_thanks_decision(commit: ParsedCommit) -> bool:
    """Get user's decision on whether to thank contributor."""
    github_username = _extract_github_username(commit)
    is_external = not any(
        domain in commit.author_email for domain in ["elementl.com", "dagsterlabs.com"]
    )

    # Show suggestion based on detection
    if github_username and is_external:
        default_msg = f" (suggested: YES - external contributor @{github_username})"
        default_choice = "y"
    else:
        default_msg = " (suggested: NO - appears to be internal)"
        default_choice = "n"

    while True:
        choice = input(f"Add thanks to contributor?{default_msg} [y/N]: ").strip().lower()

        if not choice:  # Empty input, use default
            choice = default_choice

        if choice in ["y", "yes"]:
            return True
        elif choice in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'")


def _interactive_changelog_generation(new_version: str, prev_version: str) -> str:
    """Interactive changelog generation with user review of each commit."""
    print(f"🚀 Interactive Changelog Generation for {new_version}")
    print("You'll review each commit and decide how to handle it.")
    print("Press Ctrl+C at any time to quit.\n")

    # Collect all commits first
    all_commits = []
    documented_internal = []

    internal_repo_name = str(INTERNAL_REPO.git_dir).split("/")[-2]

    for commit in _get_commits([OSS_REPO, INTERNAL_REPO], new_version, prev_version):
        if commit.ignore:
            continue
        elif commit.repo_name == internal_repo_name and commit.documented:
            documented_internal.append(commit)
        else:
            # Convert undocumented to <UNDOCUMENTED> entries for review
            if not commit.documented:
                commit = ParsedCommit(
                    issue_link=commit.issue_link,
                    changelog_category="Invalid",
                    raw_changelog_entry="<UNDOCUMENTED>",
                    raw_title=commit.raw_title,
                    author=commit.author,
                    author_email=commit.author_email,
                    repo_name=commit.repo_name,
                    ignore=False,
                )
            all_commits.append(commit)

    print(f"Found {len(all_commits)} commits to review.")
    if documented_internal:
        print(
            f"Found {len(documented_internal)} internal repo commits (will be added automatically)."
        )

    # Interactive review
    processed_commits = []

    try:
        for i, commit in enumerate(all_commits, 1):
            _print_commit_info(commit, i, len(all_commits))

            # Get user action
            action = _get_user_action()

            if action == "quit":
                print("\n⚠️  Quitting early. Generating changelog with processed commits so far...")
                break
            elif action == "ignore":
                print("✅ Skipping this commit")
                continue
            elif action == "edit":
                new_entry = _get_edited_entry()
                if new_entry:  # Only update if user provided something
                    commit = ParsedCommit(
                        issue_link=commit.issue_link,
                        changelog_category=commit.changelog_category,
                        raw_changelog_entry=new_entry,
                        raw_title=commit.raw_title,
                        author=commit.author,
                        author_email=commit.author_email,
                        repo_name=commit.repo_name,
                        ignore=False,
                    )

            # Get category (unless it's already properly categorized)
            if commit.changelog_category == "Invalid":
                category = _get_category_choice()
                commit = ParsedCommit(
                    issue_link=commit.issue_link,
                    changelog_category=category,
                    raw_changelog_entry=commit.raw_changelog_entry,
                    raw_title=commit.raw_title,
                    author=commit.author,
                    author_email=commit.author_email,
                    repo_name=commit.repo_name,
                    ignore=False,
                )

            # Get thanks decision
            should_thank = _get_thanks_decision(commit)

            # Store the thanks decision in a way we can use later
            # We'll modify the commit to include this info
            commit = ParsedCommit(
                issue_link=commit.issue_link,
                changelog_category=commit.changelog_category,
                raw_changelog_entry=commit.raw_changelog_entry,
                raw_title=commit.raw_title,
                author=commit.author,
                author_email=commit.author_email,
                repo_name=commit.repo_name,
                ignore=not should_thank,  # Repurpose ignore field to track thanks decision
            )

            processed_commits.append(commit)
            print("✅ Commit processed!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Generating changelog with processed commits so far...")

    # Generate final changelog
    header = f"# Changelog\n\n## {new_version} (core) / {_get_libraries_version(new_version)} (libraries)"

    sections = []
    if processed_commits:
        sections.append(_get_documented_section_with_thanks(processed_commits))

    if documented_internal:
        sections.append(
            f"\n\n## Internal Repository Changes\n{_get_documented_section(documented_internal)}"
        )

    return header + "".join(sections)


def _get_documented_section_with_thanks(documented: Sequence[ParsedCommit]) -> str:
    """Modified documented section that respects user's thanks decisions."""
    grouped_commits: Mapping[str, list[ParsedCommit]] = defaultdict(list)
    for commit in documented:
        grouped_commits[commit.changelog_category].append(commit)

    documented_text = ""
    for category in CATEGORIES.values():
        category_commits = grouped_commits.get(category, [])
        if not category_commits:
            continue  # Skip empty categories

        documented_text += f"\n\n### {category}\n"
        for commit in category_commits:
            entry = commit.raw_changelog_entry or commit.raw_title

            # Put PR link on separate bullet point for easier deletion
            documented_text += f"\n- {entry}\n  - {commit.issue_link}"

            # Add GitHub profile link based on user's thanks decision
            if not commit.ignore:  # User chose to thank
                github_username = _extract_github_username(commit)
                if github_username:
                    documented_text += (
                        f"\n  - [@{github_username}](https://github.com/{github_username})"
                    )
                else:
                    documented_text += f"\n  - Could not parse user (author: {commit.author}, email: {commit.author_email})"
    return documented_text


@click.command()
@click.argument("new_version", type=str, required=True)
@click.argument("prev_version", type=str, required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode to review each commit")
def generate_changelog(
    new_version: str, prev_version: Optional[str] = None, interactive: bool = False
) -> None:
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

    # Generate changelog based on mode
    if interactive:
        new_text = _interactive_changelog_generation(new_version, prev_version)
    else:
        new_text = _generate_changelog_text(new_version, prev_version)

    with open(CHANGELOG_PATH) as f:
        current_changelog = f.read()

    new_changelog = new_text + current_changelog[1:]

    with open(CHANGELOG_PATH, "w") as f:
        f.write(new_changelog)

    if interactive:
        print("\n🎉 Interactive changelog generation complete!")
        print(f"📝 Changelog updated in {CHANGELOG_PATH}")
    else:
        print(f"📝 Automatic changelog generated in {CHANGELOG_PATH}")


if __name__ == "__main__":
    generate_changelog()
