import os
import re
import sys
import termios
import tty
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from time import sleep
from typing import NamedTuple, Optional

import click
import git
import requests
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.prompt import Prompt

console = Console()

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

# Category order for display
CATEGORY_ORDER = [
    "New",
    "Bugfixes",
    "Documentation",
    "Breaking Changes",
    "Deprecations",
    "Dagster Plus",
    "dg & Components (Preview)",
    "Invalid",
]

# Enhanced categorization keywords
CATEGORY_KEYWORDS = {
    "New": [
        "add",
        "new",
        "support",
        "introduce",
        "implement",
        "create",
        "enable",
        "feature",
        "enhancement",
    ],
    "Bugfixes": [
        "fix",
        "fixed",
        "bug",
        "issue",
        "error",
        "problem",
        "resolve",
        "correct",
        "repair",
        "patch",
    ],
    "Documentation": [
        "doc",
        "documentation",
        "readme",
        "guide",
        "example",
        "tutorial",
        "docs",
        "docstring",
    ],
    "Breaking Changes": ["break", "breaking", "remove", "deprecate", "incompatible", "major"],
    "Deprecations": ["deprecate", "deprecated", "obsolete", "legacy"],
    "Dagster Plus": ["plus", "cloud", "dagster+", "enterprise", "cloud"],
}

# Package prefix detection based on file paths
PACKAGE_PREFIXES = {
    "dagster-airbyte": "airbyte",
    "dagster-airflow": "airflow",
    "dagster-aws": "aws",
    "dagster-azure": "azure",
    "dagster-celery": "celery",
    "dagster-dbt": "dbt",
    "dagster-docker": "docker",
    "dagster-fivetran": "fivetran",
    "dagster-gcp": "gcp",
    "dagster-k8s": "k8s",
    "dagster-mlflow": "mlflow",
    "dagster-pandas": "pandas",
    "dagster-postgres": "postgres",
    "dagster-pyspark": "pyspark",
    "dagster-snowflake": "snowflake",
    "dagster-spark": "spark",
    "dagster-ssh": "ssh",
    "dagster-wandb": "wandb",
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
    """Generate documented section without PR links or GitHub profiles (for internal repo changes)."""
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
            documented_text += f"\n- {entry}"
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


def _display_commit_info(
    commit: ParsedCommit, index: int, total: int, should_thank: bool, is_discarded: bool = False
) -> None:
    """Display commit information using Rich formatting."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    # Create and display progress bar
    progress = Progress(
        TextColumn("[bold blue]Progress:"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TextColumn("commits"),
    )
    progress.add_task("Processing", completed=index, total=total)
    console.print(progress)
    console.print()  # Add spacing

    # Create header
    header = Text(f"Commit {index}/{total}", style="bold blue")

    # Create main info table
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="cyan", min_width=15)
    table.add_column("Value", style="white")

    # Add commit info
    table.add_row("PR Link:", commit.issue_link)
    table.add_row("Author:", f"{commit.author} ({commit.author_email})")
    table.add_row("Title:", commit.raw_title)
    table.add_row("Category:", f"[yellow]{commit.changelog_category}[/yellow]")
    table.add_row("Entry:", commit.raw_changelog_entry or "<UNDOCUMENTED>")

    # GitHub username info
    github_username = _extract_github_username(commit)
    if github_username:
        table.add_row("GitHub:", f"@{github_username}")
        thanks_status = "[green]YES[/green]" if should_thank else "[red]NO[/red]"
        table.add_row("Thanks:", thanks_status)
    else:
        table.add_row("GitHub:", "[dim]Could not parse[/dim]")
        table.add_row("Thanks:", "[dim]N/A[/dim]")

    # Determine main panel style based on discard state
    main_border_style = "red" if is_discarded else "blue"

    # Print the table first
    console.print(Panel(table, title=header, border_style=main_border_style))

    # Create proposed action panel - show what will actually happen
    if is_discarded:
        proposed_content = "[red]SKIP THIS COMMIT[/red]\n(Will not appear in changelog)"
        proposed_title = "[bold red]Proposed Action: SKIP[/bold red]"
        proposed_border = "red"
    else:
        # Color code the category
        category_colors = {
            "New": "green",
            "Bugfixes": "red",
            "Documentation": "blue",
            "Breaking Changes": "magenta",
            "Deprecations": "yellow",
            "Dagster Plus": "cyan",
            "dg & Components (Preview)": "bright_blue",
            "Invalid": "white",
        }
        category_color = category_colors.get(commit.changelog_category, "white")

        proposed_entry = commit.raw_changelog_entry or commit.raw_title
        if should_thank and github_username:
            proposed_entry += (
                f" (thanks [@{github_username}](https://github.com/{github_username})!)"
            )

        proposed_content = f"[green]ADD TO CHANGELOG:[/green]\n{proposed_entry}"
        proposed_title = f"[bold green]Proposed Entry:[/bold green] [{category_color}]{commit.changelog_category}[/{category_color}]"
        proposed_border = "green"

    # Show proposed action in a sub-panel
    proposed_panel = Panel(
        proposed_content,
        title=proposed_title,
        border_style=proposed_border,
        padding=(1, 2),
    )
    console.print(proposed_panel)

    # Display controls - Enter always executes the proposed action
    controls = Text("\nControls: ")
    controls.append("[Enter]", style="bold green")
    if is_discarded:
        controls.append(" Execute (Skip)  ")
    else:
        controls.append(" Execute (Add)  ")
    controls.append("[c]", style="bold yellow")
    controls.append(" Change category  ")
    controls.append("[e]", style="bold cyan")
    controls.append(" Edit text  ")
    controls.append("[t]", style="bold magenta")
    controls.append(" Toggle thanks  ")
    controls.append("[d]", style="bold red")
    controls.append(" Toggle skip  ")
    controls.append("[q]", style="bold white")
    controls.append(" Quit")
    console.print(controls)


def _get_category_choice_interactive() -> Optional[str]:
    """Get user's category choice with interactive menu."""
    # Note: We can't access the commit here, so we'll show all categories
    # but add a note about Dagster Plus being for internal repo only
    categories = [
        "New",
        "Bugfixes",
        "Documentation",
        "Dagster Plus (Internal repo only)",
        "Breaking Changes",
        "Deprecations",
    ]

    console.print("\n[bold cyan]Select category:[/bold cyan]")
    for i, cat in enumerate(categories, 1):
        console.print(f"  {i}) {cat}")

    choice = Prompt.ask("Enter number (or press Enter to cancel)", default="")

    if not choice:
        return None

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(categories):
            category = categories[idx]
            # Remove the note from Dagster Plus
            if category.startswith("Dagster Plus"):
                return "Dagster Plus"
            return category
    except ValueError:
        pass

    console.print("[red]Invalid choice[/red]")
    return None


def _get_edited_entry_interactive(current_entry: str) -> Optional[str]:
    """Get user's edited changelog entry interactively."""
    console.print(f"\n[bold cyan]Current entry:[/bold cyan] {current_entry}")
    new_entry = Prompt.ask("Enter new text (or press Enter to cancel)", default="")
    return new_entry if new_entry else None


def _smart_guess_category(commit: ParsedCommit) -> str:
    """Use keywords to guess the most appropriate category for a commit."""
    text_to_check = (commit.raw_changelog_entry or commit.raw_title).lower()
    internal_repo_name = str(INTERNAL_REPO.git_dir).split("/")[-2]
    is_internal_repo = commit.repo_name == internal_repo_name

    # Score each category based on keyword matches
    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        # Only allow "Dagster Plus" category for internal repo commits
        if category == "Dagster Plus" and not is_internal_repo:
            continue

        score = sum(1 for keyword in keywords if keyword in text_to_check)
        if score > 0:
            category_scores[category] = score

    if not category_scores:
        return "Invalid"  # No matches found

    # Return the category with the highest score
    return max(category_scores, key=category_scores.get)


def _get_package_prefix(commit: ParsedCommit) -> Optional[str]:
    """Detect package prefix from issue URL or commit info."""
    # For now, we could enhance this by parsing commit diffs or file paths
    # but the GitHub API would be needed for that level of detail
    return None


# Removed unused Rich layout functions - using simpler single-pass approach


def _interactive_changelog_generation(new_version: str, prev_version: str) -> str:
    """Single-pass interactive changelog generation with keyboard shortcuts."""
    console.print(f"🚀 Interactive Changelog Generation for {new_version}", style="bold blue")
    console.print("Review each commit with keyboard shortcuts for quick editing\n")

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
            # Only include undocumented commits from OSS repo (dagster), not internal
            if not commit.documented and commit.repo_name == "dagster":
                updated_commit = ParsedCommit(
                    issue_link=commit.issue_link,
                    changelog_category="Invalid",
                    raw_changelog_entry="<UNDOCUMENTED>",
                    raw_title=commit.raw_title,
                    author=commit.author,
                    author_email=commit.author_email,
                    repo_name=commit.repo_name,
                    ignore=False,
                )
                all_commits.append(updated_commit)
            elif commit.documented:
                all_commits.append(commit)

    console.print(f"Found {len(all_commits)} commits to review.", style="green")
    if documented_internal:
        console.print(
            f"Found {len(documented_internal)} internal repo commits (auto-included).", style="blue"
        )

    # Smart categorization and initial thanks detection
    console.print("\n🤖 Running smart categorization and contributor detection...", style="yellow")
    processed_commits = []

    for commit in all_commits:
        # Smart category guess if needed
        if commit.changelog_category == "Invalid":
            guessed_category = _smart_guess_category(commit)
            commit = ParsedCommit(  # noqa: PLW2901
                issue_link=commit.issue_link,
                changelog_category=guessed_category,
                raw_changelog_entry=commit.raw_changelog_entry,
                raw_title=commit.raw_title,
                author=commit.author,
                author_email=commit.author_email,
                repo_name=commit.repo_name,
                ignore=False,
            )
        processed_commits.append(commit)

    # Interactive review - single pass
    console.print("\n📝 Individual Commit Review", style="bold cyan")
    console.print("Use keyboard shortcuts to quickly modify each commit\n")

    final_commits = []

    try:
        for i, commit in enumerate(processed_commits, 1):
            # Detect if this should be thanked (external contributor)
            github_username = _extract_github_username(commit)
            is_external = not any(
                domain in commit.author_email for domain in ["elementl.com", "dagsterlabs.com"]
            )
            should_thank = bool(github_username and is_external)

            # Default to discarding Invalid/undocumented commits
            is_discarded = commit.changelog_category == "Invalid" or not commit.raw_changelog_entry

            while True:  # Allow multiple edits to same commit
                console.clear()
                _display_commit_info(commit, i, len(processed_commits), should_thank, is_discarded)

                # Get single character input without Enter
                action_text = "Execute (Add)" if not is_discarded else "Execute (Skip)"
                console.print(
                    f"\n[bold]Press a key:[/bold] [Enter]={action_text}, [c]=category, [e]=edit, [t]=thanks, [d]=toggle skip, [q]=quit"
                )

                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setraw(sys.stdin.fileno())
                    action = sys.stdin.read(1).lower()
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

                # Handle Enter key (carriage return)
                if ord(action) == 13 or ord(action) == 10:
                    action = "accept"

                if action in ["accept", "a", "\r", "\n"] or ord(action) == 13:
                    # Execute the proposed action
                    if not is_discarded:
                        # Add to changelog
                        final_commit = ParsedCommit(
                            issue_link=commit.issue_link,
                            changelog_category=commit.changelog_category,
                            raw_changelog_entry=commit.raw_changelog_entry,
                            raw_title=commit.raw_title,
                            author=commit.author,
                            author_email=commit.author_email,
                            repo_name=commit.repo_name,
                            ignore=not should_thank,  # Use ignore field to track thanks
                        )
                        final_commits.append(final_commit)
                        console.print("✅ Added to changelog", style="green")
                    else:
                        # Skip this commit
                        console.print("⏭️ Skipped", style="yellow")
                    break

                elif action in ["c", "category"]:
                    # Change category
                    new_category = _get_category_choice_interactive()
                    if new_category:
                        commit = ParsedCommit(  # noqa: PLW2901
                            issue_link=commit.issue_link,
                            changelog_category=new_category,
                            raw_changelog_entry=commit.raw_changelog_entry,
                            raw_title=commit.raw_title,
                            author=commit.author,
                            author_email=commit.author_email,
                            repo_name=commit.repo_name,
                            ignore=False,
                        )
                        console.print(
                            f"✅ Category changed to [yellow]{new_category}[/yellow]", style="green"
                        )
                    # Continue loop to show updated commit

                elif action in ["e", "edit"]:
                    # Edit text
                    current_entry = commit.raw_changelog_entry or commit.raw_title
                    new_entry = _get_edited_entry_interactive(current_entry)
                    if new_entry:
                        commit = ParsedCommit(  # noqa: PLW2901
                            issue_link=commit.issue_link,
                            changelog_category=commit.changelog_category,
                            raw_changelog_entry=new_entry,
                            raw_title=commit.raw_title,
                            author=commit.author,
                            author_email=commit.author_email,
                            repo_name=commit.repo_name,
                            ignore=False,
                        )
                        console.print("✅ Text updated", style="green")
                    # Continue loop to show updated commit

                elif action in ["t", "thanks", "toggle"]:
                    # Toggle thanks
                    should_thank = not should_thank
                    status = "[green]ON[/green]" if should_thank else "[red]OFF[/red]"
                    console.print(f"✅ Thanks toggled {status}", style="green")
                    # Continue loop to show updated commit

                elif action in ["d", "discard", "toggle"]:
                    # Toggle discard state
                    is_discarded = not is_discarded
                    status = "❌ Discarded" if is_discarded else "✅ Un-discarded"
                    console.print(status, style="red" if is_discarded else "green")
                    # Continue loop to show updated display

                elif action in ["q", "quit"]:
                    console.print("\n⚠️  Quitting early...", style="yellow")
                    raise KeyboardInterrupt

                else:
                    console.print(f"[red]Unknown action: {action}[/red]")
                    console.print(
                        "Use: [Enter]=accept, [c]=category, [e]=edit, [t]=thanks, [d]=discard, [q]=quit"
                    )
                    # Continue loop

    except KeyboardInterrupt:
        console.print(
            "\n\n⚠️  Interrupted by user. Generating changelog with processed commits so far...",
            style="yellow",
        )

    # Generate final changelog
    header = f"# Changelog\n\n## {new_version} (core) / {_get_libraries_version(new_version)} (libraries)"

    console.print(
        f"\n✅ Processed {len(final_commits)} commits for final changelog.", style="bold green"
    )

    sections = []
    if final_commits:
        sections.append(_get_documented_section_with_thanks(final_commits))

    if documented_internal:
        sections.append(
            f"\n\n## Internal Repository Changes\n{_get_documented_section(documented_internal)}"
        )

    return header + "".join(sections)


def _get_documented_section_with_thanks(documented: Sequence[ParsedCommit]) -> str:
    """Generate documented section with thanks integrated into commit messages."""
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

            # Add thanks directly to the commit message if user chose to thank
            if not commit.ignore:  # User chose to thank
                github_username = _extract_github_username(commit)
                if github_username:
                    entry += (
                        f" (thanks [@{github_username}](https://github.com/{github_username})!)"
                    )

            documented_text += f"\n- {entry}"
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
        console.print("\n🎉 Interactive changelog generation complete!", style="bold green")
        console.print(f"📝 Changelog updated in {CHANGELOG_PATH}")
    else:
        console.print(f"📝 Automatic changelog generated in {CHANGELOG_PATH}")


if __name__ == "__main__":
    generate_changelog()
