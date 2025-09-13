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
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

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
    prefix: Optional[str]  # Library prefix like [dagster-dbt], [ui], etc.
    ignore: bool

    @property
    def documented(self) -> bool:
        return bool(self.raw_changelog_entry)


def _clean_changelog_entry(text: str) -> str:
    """Clean up changelog entry by removing leading characters and whitespace."""
    if not text:
        return text

    # Strip whitespace
    text = text.strip()

    # Remove common leading characters people add
    prefixes_to_remove = ["> ", "- ", "* ", "+ "]
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
            break

    return text


def _extract_prefix_from_text(text: str) -> tuple[Optional[str], str]:
    """Extract library prefix from changelog text and return (prefix, cleaned_text).

    Examples:
        "[dagster-dbt] Fixed issue" -> ("dagster-dbt", "Fixed issue")
        "[ui] Updated interface" -> ("ui", "Updated interface")
        "Regular entry" -> (None, "Regular entry")
    """
    import re

    if not text:
        return None, text

    # Look for prefix pattern at the start: [something]
    match = re.match(r"^\[([^\]]+)\]\s*(.*)", text.strip())
    if match:
        prefix = match.group(1)
        remaining_text = match.group(2)
        return prefix, remaining_text

    return None, text


def _is_valid_prefix(prefix: Optional[str]) -> bool:
    """Check if prefix is valid: None, 'ui', or 'dagster-*'."""
    if prefix is None:
        return True
    if prefix == "ui":
        return True
    if prefix.startswith("dagster-"):
        return True
    return False


def _detect_library_prefix(
    commit_title: str, commit_entry: Optional[str], repo_name: str
) -> Optional[str]:
    """Detect appropriate library prefix based on commit content and file changes."""
    # First try to extract existing prefix from changelog entry or title
    if commit_entry:
        prefix, _ = _extract_prefix_from_text(commit_entry)
        if _is_valid_prefix(prefix):
            return prefix

    prefix, _ = _extract_prefix_from_text(commit_title)
    if _is_valid_prefix(prefix):
        return prefix

    # Check for UI-related changes
    ui_keywords = [
        "ui",
        "webserver",
        "frontend",
        "react",
        "graphql",
        "web",
        "browser",
        "interface",
        "dashboard",
    ]
    text_to_check = f"{commit_title} {commit_entry or ''}".lower()

    if any(keyword in text_to_check for keyword in ui_keywords):
        return "ui"

    # Check for library-specific keywords in commit text
    for lib_name in PACKAGE_PREFIXES.keys():
        if lib_name.replace("dagster-", "") in text_to_check:
            return lib_name
        # Also check without the dagster- prefix
        lib_short = lib_name.replace("dagster-", "")
        if lib_short in text_to_check:
            return lib_name

    # No specific library detected
    return None


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

    # Clean and extract prefix from changelog entry
    cleaned_entry = None
    detected_prefix = None
    if raw_changelog_entry:
        cleaned_entry = _clean_changelog_entry(raw_changelog_entry)
        detected_prefix, cleaned_entry = _extract_prefix_from_text(cleaned_entry)

    # If no prefix found in entry, try to detect from commit content
    if not detected_prefix:
        detected_prefix = _detect_library_prefix(title, raw_changelog_entry, repo_name)

    return ParsedCommit(
        issue_link=issue_link,
        changelog_category=CATEGORIES.get(changelog_category, "Invalid"),
        raw_changelog_entry=cleaned_entry,
        raw_title=title,
        author=str(commit.author.name),
        author_email=str(commit.author.email),
        repo_name=repo_name,
        prefix=detected_prefix,
        ignore=ignore,
    )


def _get_documented_section(documented: Sequence[ParsedCommit]) -> str:
    """Generate documented section without PR links or GitHub profiles (for internal repo changes)."""
    grouped_commits: Mapping[str, list[ParsedCommit]] = defaultdict(list)
    for commit in documented:
        # Skip Invalid category completely
        if commit.changelog_category != "Invalid":
            grouped_commits[commit.changelog_category].append(commit)

    documented_text = ""
    # Filter out "Invalid" from categories
    valid_categories = [cat for cat in CATEGORIES.values() if cat != "Invalid"]

    for category in valid_categories:
        category_commits = grouped_commits.get(category, [])
        if not category_commits:
            continue  # Skip empty categories

        # Sort commits within category by prefix
        category_commits.sort(key=_prefix_sort_key)

        documented_text += f"\n\n### {category}\n"
        for commit in category_commits:
            entry = commit.raw_changelog_entry or commit.raw_title

            # Add prefix if present
            if commit.prefix:
                entry = f"[{commit.prefix}] {entry}"

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
        undocumented_commit = commit._replace(
            changelog_category="Invalid", raw_changelog_entry="<UNDOCUMENTED>", ignore=False
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


def _create_commit_display(
    commit: ParsedCommit,
    index: int,
    total: int,
    should_thank: bool,
    is_discarded: bool = False,
    feedback_message: str = "",
) -> Panel:
    """Create a renderable display for commit information using Rich formatting."""
    from rich.panel import Panel

    # Create and display progress bar
    progress = Progress(
        TextColumn("[bold blue]Progress:"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TextColumn("commits"),
    )
    progress.add_task("Processing", completed=index, total=total)

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
    table.add_row(
        "Prefix:", f"[cyan]{commit.prefix}[/cyan]" if commit.prefix else "[dim]None[/dim]"
    )
    # Show entry with special formatting for undocumented
    entry_text = commit.raw_changelog_entry or "[red]<UNDOCUMENTED>[/red]"
    table.add_row("Entry:", entry_text)

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
    main_border_style = "yellow" if is_discarded else "blue"

    # Create proposed action panel - show what will actually happen
    is_undocumented = (
        not commit.raw_changelog_entry or commit.raw_changelog_entry == "<UNDOCUMENTED>"
    )

    if is_discarded:
        proposed_content = "[red]SKIP THIS COMMIT[/red]\n(Will not appear in changelog)"
        proposed_title = "[bold red]Proposed Action: SKIP[/bold red]"
        proposed_border = "red"
    elif is_undocumented:
        proposed_content = "[red]CANNOT ACCEPT[/red]\n[dim]Must add changelog entry first[/dim]"
        proposed_title = "[bold red]Status: UNDOCUMENTED[/bold red]"
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
                f" (Thanks, [@{github_username}](https://github.com/{github_username})!)"
            )

        # Add prefix if present
        if commit.prefix:
            proposed_entry = f"[{commit.prefix}] {proposed_entry}"

        proposed_content = f"[green]ADD TO CHANGELOG:[/green]\n- {proposed_entry}"
        proposed_title = f"[bold green]Proposed Entry:[/bold green] [{category_color}]{commit.changelog_category}[/{category_color}]"
        proposed_border = "green"

    # Show proposed action in a sub-panel
    proposed_panel = Panel(
        proposed_content,
        title=proposed_title,
        border_style=proposed_border,
        padding=(1, 2),
    )

    # Display controls - Enter behavior depends on state
    controls = Text("\nControls: ")
    if is_undocumented and not is_discarded:
        controls.append("[Enter]", style="bold red")
        controls.append(" Cannot Accept  ")
    else:
        controls.append("[Enter]", style="bold green")
        if is_discarded:
            controls.append(" Execute (Skip)  ")
        else:
            controls.append(" Execute (Add)  ")
    controls.append("[c]", style="bold yellow")
    controls.append(" Change category  ")
    controls.append("[p]", style="bold cyan")
    controls.append(" Edit prefix  ")
    controls.append("[e]", style="bold cyan")
    controls.append(" Edit text  ")
    controls.append("[t]", style="bold magenta")
    controls.append(" Toggle thanks  ")
    controls.append("[d]", style="bold red")
    controls.append(" Toggle discard  ")
    controls.append("[q]", style="bold white")
    controls.append(" Quit")

    # Create the main display with progress, table, proposed action, and controls
    from rich import box

    # Combine all components into a single panel
    main_content = Table(show_header=False, box=None, padding=0)
    main_content.add_column(justify="left")

    # Add progress bar FIRST
    main_content.add_row(progress)
    main_content.add_row("")  # spacing

    # Always add feedback area after progress bar
    feedback_text = feedback_message if feedback_message else "Ready for action"
    feedback_panel = Panel(
        Text(feedback_text, style="bold" if feedback_message else "dim"),
        title="Latest Action",
        border_style="cyan",
        padding=(0, 1),
    )
    main_content.add_row(feedback_panel)
    main_content.add_row("")  # spacing

    # Add main info table
    main_content.add_row(Panel(table, title=header, border_style=main_border_style))
    main_content.add_row("")  # spacing

    # Add proposed action panel
    main_content.add_row(proposed_panel)

    # Add controls
    main_content.add_row(controls)

    return Panel(main_content, box=box.SQUARE, padding=(1, 2))


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
    """Get user's edited changelog entry interactively with pre-populated text."""
    import readline

    # Pre-fill the readline buffer with current text
    def pre_input_hook():
        readline.insert_text(current_entry)
        readline.redisplay()

    readline.set_pre_input_hook(pre_input_hook)

    try:
        console.print("\n[bold cyan]Edit entry:[/bold cyan]")
        new_entry = input("Text: ")
        return new_entry if new_entry.strip() else None
    finally:
        # Clean up the hook
        readline.set_pre_input_hook(None)


def _get_prefix_choice_interactive(current_prefix: Optional[str]) -> Optional[str]:
    """Get user's prefix choice with interactive menu."""
    # Common prefixes - only dagster libraries and ui
    common_prefixes = [
        None,  # No prefix (most common)
        "ui",
        "dagster-dbt",
        "dagster-airbyte",
        "dagster-aws",
        "dagster-azure",
        "dagster-gcp",
        "dagster-k8s",
        "dagster-snowflake",
    ]

    console.print(f"\n[bold cyan]Current prefix:[/bold cyan] {current_prefix or '(none)'}")
    console.print("\n[bold cyan]Select prefix:[/bold cyan]")
    for i, prefix in enumerate(common_prefixes, 1):
        display_name = prefix or "(no prefix)"
        console.print(f"  {i}) {display_name}")

    console.print("  c) Custom prefix")

    choice = Prompt.ask("Enter number or 'c' for custom (or press Enter to cancel)", default="")

    if not choice:
        return current_prefix  # No change

    if choice.lower() == "c":
        custom_prefix = Prompt.ask("Enter custom prefix (without brackets)", default="")
        return custom_prefix if custom_prefix else current_prefix

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(common_prefixes):
            return common_prefixes[idx]
    except ValueError:
        pass

    console.print("[red]Invalid choice[/red]")
    return current_prefix  # No change


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
                updated_commit = commit._replace(
                    changelog_category="Invalid", raw_changelog_entry="<UNDOCUMENTED>", ignore=False
                )
                all_commits.append(updated_commit)
            elif commit.documented:
                all_commits.append(commit)

    # Smart categorization and initial thanks detection
    processed_commits = []

    for commit in all_commits:
        # Smart category guess if needed
        if commit.changelog_category == "Invalid":
            guessed_category = _smart_guess_category(commit)
            commit = commit._replace(changelog_category=guessed_category, ignore=False)  # noqa: PLW2901
        processed_commits.append(commit)

    # Show initial summary
    console.print(f"\n🚀 Interactive Changelog Generation for {new_version}", style="bold blue")
    console.print(f"Found {len(processed_commits)} commits to review.", style="green")
    if documented_internal:
        console.print(
            f"Found {len(documented_internal)} internal repo commits (auto-included).", style="blue"
        )
    console.print("Use keyboard shortcuts to quickly modify each commit\n", style="cyan")

    final_commits = []

    # Create single persistent Live display
    current_commit = processed_commits[0] if processed_commits else None

    if not processed_commits:
        return "No commits to process."

    # Initial setup for first commit
    github_username = _extract_github_username(current_commit)
    is_external = not any(
        domain in current_commit.author_email for domain in ["elementl.com", "dagsterlabs.com"]
    )
    should_thank = bool(github_username and is_external)
    is_discarded = (
        current_commit.changelog_category == "Invalid" or not current_commit.raw_changelog_entry
    )
    feedback_message = ""

    # Create initial display
    display_panel = _create_commit_display(
        current_commit, 1, len(processed_commits), should_thank, is_discarded, feedback_message
    )

    try:
        with Live(display_panel, auto_refresh=False, console=console, screen=False) as live:
            i = 1
            commit = current_commit
            while i <= len(processed_commits):
                commit = processed_commits[i - 1]  # Convert to 0-based index

                # Setup commit state
                github_username = _extract_github_username(commit)
                is_external = not any(
                    domain in commit.author_email for domain in ["elementl.com", "dagsterlabs.com"]
                )
                should_thank = bool(github_username and is_external)
                is_discarded = (
                    commit.changelog_category == "Invalid" or not commit.raw_changelog_entry
                )
                feedback_message = ""

                # Update display for current commit
                display_panel = _create_commit_display(
                    commit, i, len(processed_commits), should_thank, is_discarded, feedback_message
                )
                live.update(display_panel)
                live.refresh()

                while True:  # Allow multiple edits to same commit
                    try:
                        # Get single character input without Enter
                        old_settings = termios.tcgetattr(sys.stdin)
                        try:
                            tty.setraw(sys.stdin.fileno())
                            action = sys.stdin.read(1).lower()
                        finally:
                            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

                        # Handle Enter key (carriage return)
                        if ord(action) == 13 or ord(action) == 10:
                            action = "accept"

                        if (
                            action == "a"
                            or action == "accept"
                            or ord(action) == 13
                            or ord(action) == 10
                        ):
                            # Check if commit is undocumented and not discarded
                            is_undocumented = (
                                not commit.raw_changelog_entry
                                or commit.raw_changelog_entry == "<UNDOCUMENTED>"
                            )
                            if is_undocumented and not is_discarded:
                                feedback_message = "❌ Cannot accept undocumented commit. Please add changelog entry first or discard it."
                                display_panel = _create_commit_display(
                                    commit,
                                    i,
                                    len(processed_commits),
                                    should_thank,
                                    is_discarded,
                                    feedback_message,
                                )
                                live.update(display_panel)
                                live.refresh()
                                # Continue loop to show same commit
                            elif not is_discarded:
                                # Add to changelog
                                final_commit = commit._replace(
                                    ignore=not should_thank
                                )  # Use ignore field to track thanks
                                final_commits.append(final_commit)
                                feedback_message = "✅ Added to changelog"
                                display_panel = _create_commit_display(
                                    commit,
                                    i,
                                    len(processed_commits),
                                    should_thank,
                                    is_discarded,
                                    feedback_message,
                                )
                                live.update(display_panel)
                                live.refresh()
                                i += 1  # Move to next commit
                                break
                            else:
                                # Skip this commit
                                feedback_message = "⏭️ Skipped"
                                display_panel = _create_commit_display(
                                    commit,
                                    i,
                                    len(processed_commits),
                                    should_thank,
                                    is_discarded,
                                    feedback_message,
                                )
                                live.update(display_panel)
                                live.refresh()
                                i += 1  # Move to next commit
                                break

                        elif action == "c":
                            # Change category - temporarily stop Live for interactive input
                            live.stop()
                            new_category = _get_category_choice_interactive()
                            if new_category:
                                commit = commit._replace(
                                    changelog_category=new_category, ignore=False
                                )
                                # Update the commit in the processed_commits list
                                processed_commits[i - 1] = commit
                                feedback_message = f"✅ Category changed to {new_category}"
                            else:
                                feedback_message = "Category change cancelled"

                            # Update display with new category
                            display_panel = _create_commit_display(
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
                            # Restart Live with updated display
                            live.start()
                            live.update(display_panel)
                            live.refresh()
                            # Continue loop to show updated commit

                        elif action == "p":
                            # Edit prefix - temporarily stop Live for interactive input
                            live.stop()
                            new_prefix = _get_prefix_choice_interactive(commit.prefix)
                            if new_prefix != commit.prefix:
                                commit = commit._replace(prefix=new_prefix, ignore=False)
                                # Update the commit in the processed_commits list
                                processed_commits[i - 1] = commit
                                prefix_display = new_prefix or "(none)"
                                feedback_message = f"✅ Prefix changed to {prefix_display}"
                            else:
                                feedback_message = "Prefix change cancelled"

                            # Update display with new prefix
                            display_panel = _create_commit_display(
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
                            # Restart Live with updated display
                            live.start()
                            live.update(display_panel)
                            live.refresh()
                            # Continue loop to show updated commit

                        elif action == "e":
                            # Edit text - temporarily stop Live for interactive input
                            live.stop()
                            current_entry = commit.raw_changelog_entry or commit.raw_title
                            new_entry = _get_edited_entry_interactive(current_entry)
                            if new_entry:
                                # Clean and extract prefix from new entry
                                cleaned_entry = _clean_changelog_entry(new_entry)
                                detected_prefix, cleaned_entry = _extract_prefix_from_text(
                                    cleaned_entry
                                )

                                # Only use detected prefix if it's valid
                                final_prefix = (
                                    detected_prefix
                                    if _is_valid_prefix(detected_prefix)
                                    else commit.prefix
                                )

                                commit = commit._replace(
                                    raw_changelog_entry=cleaned_entry,
                                    prefix=final_prefix,
                                    ignore=False,
                                )
                                # Update the commit in the processed_commits list
                                processed_commits[i - 1] = commit
                                feedback_message = "✅ Text updated"
                            else:
                                feedback_message = "Text edit cancelled"

                            # Update display with new text
                            display_panel = _create_commit_display(
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
                            # Restart Live with updated display
                            live.start()
                            live.update(display_panel)
                            live.refresh()
                            # Continue loop to show updated commit

                        elif action == "t":
                            # Toggle thanks
                            should_thank = not should_thank
                            status = "ON" if should_thank else "OFF"
                            feedback_message = f"✅ Thanks toggled {status}"
                            # Update display with new thanks status
                            display_panel = _create_commit_display(
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
                            live.update(display_panel)
                            live.refresh()
                            # Continue loop to show updated commit

                        elif action == "d":
                            # Toggle discard state
                            is_discarded = not is_discarded
                            status = "❌ Discarded" if is_discarded else "✅ Un-discarded"
                            feedback_message = status
                            # Update display with new discard status
                            display_panel = _create_commit_display(
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
                            live.update(display_panel)
                            live.refresh()
                            # Continue loop to show updated display

                        elif action == "q":
                            feedback_message = "⚠️  Quitting early..."
                            display_panel = _create_commit_display(
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
                            live.update(display_panel)
                            raise KeyboardInterrupt

                        else:
                            feedback_message = f"Unknown action: {action}. Use: [Enter]=accept, [c]=category, [p]=prefix, [e]=edit, [t]=thanks, [d]=discard, [q]=quit"
                            display_panel = _create_commit_display(
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
                            live.update(display_panel)
                            live.refresh()
                            # Continue loop
                    except KeyboardInterrupt:
                        # Handle Ctrl+C gracefully
                        feedback_message = "⚠️  Interrupted by user..."
                        display_panel = _create_commit_display(
                            commit,
                            i,
                            len(processed_commits),
                            should_thank,
                            is_discarded,
                            feedback_message,
                        )
                        live.update(display_panel)
                        live.refresh()
                        raise KeyboardInterrupt

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


def _prefix_sort_key(commit: ParsedCommit) -> tuple:
    """Sort key for commits within a category: no prefix first, then [ui], then others by reverse length."""
    if not commit.prefix:
        return (0, "")  # No prefix comes first
    elif commit.prefix == "ui":
        return (1, commit.prefix)  # [ui] comes second
    else:
        return (
            2,
            -len(commit.prefix),
            commit.prefix,
        )  # Others sorted by reverse length, then alphabetically


def _get_documented_section_with_thanks(documented: Sequence[ParsedCommit]) -> str:
    """Generate documented section with thanks integrated into commit messages."""
    grouped_commits: Mapping[str, list[ParsedCommit]] = defaultdict(list)
    for commit in documented:
        # Skip Invalid category completely
        if commit.changelog_category != "Invalid":
            grouped_commits[commit.changelog_category].append(commit)

    documented_text = ""
    # Filter out "Invalid" from categories
    valid_categories = [cat for cat in CATEGORIES.values() if cat != "Invalid"]

    for category in valid_categories:
        category_commits = grouped_commits.get(category, [])
        if not category_commits:
            continue  # Skip empty categories

        # Sort commits within category by prefix
        category_commits.sort(key=_prefix_sort_key)

        documented_text += f"\n\n### {category}\n"
        for commit in category_commits:
            entry = commit.raw_changelog_entry or commit.raw_title

            # Add prefix if present
            if commit.prefix:
                entry = f"[{commit.prefix}] {entry}"

            # Add thanks directly to the commit message if user chose to thank
            if not commit.ignore:  # User chose to thank
                github_username = _extract_github_username(commit)
                if github_username:
                    entry += (
                        f" (Thanks, [@{github_username}](https://github.com/{github_username})!)"
                    )

            documented_text += f"\n- {entry}"
    return documented_text


@click.command()
@click.argument("new_version", type=str, required=True)
@click.argument("prev_version", type=str, required=False)
def generate_changelog(new_version: str, prev_version: Optional[str] = None) -> None:
    if prev_version is None:
        prev_version = _get_previous_version(new_version)

    # Show loading indicator during setup
    from rich.text import Text

    loading_text = Text("Setting up branches and parsing commits...", style="bold blue")
    with Live(loading_text, auto_refresh=True, refresh_per_second=4, console=console) as live:
        # ensure that the release branches are available locally
        for repo in [OSS_REPO, INTERNAL_REPO]:
            live.update(
                Text(
                    f"Checking out branches for {repo.git_dir.split('/')[-2]}...", style="bold blue"
                )
            )
            repo.git.checkout("master")
            repo.git.pull()
            repo.git.checkout(f"release-{prev_version}")
            repo.git.pull()
            repo.git.checkout(f"release-{new_version}")
            repo.git.pull()
            repo.git.checkout("master")

        live.update(Text("Parsing commits and preparing interactive review...", style="bold blue"))

    # Generate changelog in interactive mode
    new_text = _interactive_changelog_generation(new_version, prev_version)

    with open(CHANGELOG_PATH) as f:
        current_changelog = f.read()

    new_changelog = new_text + current_changelog[1:]

    with open(CHANGELOG_PATH, "w") as f:
        f.write(new_changelog)

    console.print("\n🎉 Interactive changelog generation complete!", style="bold green")
    console.print(f"📝 Changelog updated in {CHANGELOG_PATH}")


if __name__ == "__main__":
    generate_changelog()
