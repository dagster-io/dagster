import os
import re
import readline
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
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
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

# Category order for display
CATEGORY_ORDER = [
    "New",
    "Bugfixes",
    "Documentation",
    "Dagster Plus",
]


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


def _fetch_github_username_from_pr(pr_url: str) -> Optional[str]:
    """Fetch GitHub username from PR using GitHub API."""
    try:
        # Parse PR URL to extract owner, repo, and PR number
        # Expected format: https://github.com/owner/repo/pull/123
        # Use regex to ensure github.com is the hostname, not just anywhere in the URL
        if not re.match(r"https?://(?:www\.)?github\.com/", pr_url):
            return None
        url_parts = pr_url.split("/")
        if len(url_parts) >= 6:
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
    if commit.issue_link:
        # Extract the URL from the markdown link [#123](https://github.com/...)
        url_match = re.search(r"\(([^)]+)\)", commit.issue_link)
        if url_match:
            pr_url = url_match.group(1)
            # Check if it's a proper GitHub URL
            if re.match(r"https?://(?:www\.)?github\.com/", pr_url):
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
    ignore = False
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
            # Just collect the changelog entry text, ignore category checkboxes
            if not line.lower().startswith("- ["):
                raw_changelog_entry_lines.append(line.strip())
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

    # Simple UI detection
    if not detected_prefix:
        text_to_check = f"{title} {raw_changelog_entry or ''}".lower()
        if any(
            word in text_to_check for word in ["ui", "webserver", "frontend", "react", "graphql"]
        ):
            detected_prefix = "ui"

    # Create the commit object first
    parsed_commit = ParsedCommit(
        issue_link=issue_link,
        changelog_category="New",  # Will be set by guessing logic
        raw_changelog_entry=cleaned_entry,
        raw_title=title,
        author=str(commit.author.name),
        author_email=str(commit.author.email),
        repo_name=repo_name,
        prefix=detected_prefix,
        ignore=ignore,
    )

    # Use guessing logic to determine category
    guessed_category = _guess_category(parsed_commit)
    return parsed_commit._replace(changelog_category=guessed_category)


def _get_documented_section(documented: Sequence[ParsedCommit]) -> str:
    """Generate documented section without PR links or GitHub profiles (for internal repo changes)."""
    grouped_commits: Mapping[str, list[ParsedCommit]] = defaultdict(list)
    for commit in documented:
        grouped_commits[commit.changelog_category].append(commit)

    documented_text = ""

    for category in CATEGORY_ORDER:
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


def _create_commit_display(
    commit: ParsedCommit,
    index: int,
    total: int,
    should_thank: bool,
    is_discarded: bool = False,
    feedback_message: str = "",
) -> Panel:
    """Create a renderable display for commit information using Rich formatting."""
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
        # Category will be shown in the content

        proposed_entry = commit.raw_changelog_entry or commit.raw_title
        # Add prefix if present
        if commit.prefix:
            proposed_entry = f"[{commit.prefix}] {proposed_entry}"

        # Build colored proposed entry
        colored_category = f"[yellow]### {commit.changelog_category}[/yellow]"
        display_entry = proposed_entry
        if commit.prefix:
            display_entry = (
                f"[cyan]\\[{commit.prefix}][/cyan] {commit.raw_changelog_entry or commit.raw_title}"
            )
        if should_thank and github_username:
            display_entry += f" [magenta](Thanks, \\[@{github_username}](https://github.com/{github_username})!)[/magenta]"

        proposed_content = (
            f"[green]ADD TO CHANGELOG:[/green]\n\n{colored_category}\n\n- {display_entry}"
        )
        proposed_title = "[bold green]Proposed Entry[/bold green]"
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
    controls.append(" Cycle category  ")
    controls.append("[p]", style="bold cyan")
    controls.append(" Edit prefix  ")
    controls.append("[e]", style="bold green")
    controls.append(" Edit text  ")
    controls.append("[t]", style="bold magenta")
    controls.append(" Toggle thanks  ")
    controls.append("[d]", style="bold red")
    controls.append(" Toggle discard  ")
    controls.append("[q]", style="bold white")
    controls.append(" Quit")

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
        title="Message",
        border_style="blue",
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


def _cycle_category(current_category: str, is_internal_repo: bool = False) -> str:
    """Cycle to the next category in the list."""
    if is_internal_repo:
        categories = ["New", "Bugfixes", "Documentation", "Dagster Plus"]
    else:
        categories = ["New", "Bugfixes", "Documentation"]

    try:
        current_index = categories.index(current_category)
        next_index = (current_index + 1) % len(categories)
        return categories[next_index]
    except ValueError:
        # If current category not found, default to first one
        return categories[0]


def _get_edited_entry_interactive(current_entry: str) -> Optional[str]:
    """Get user's edited changelog entry with simple prompt."""

    def pre_input_hook():
        readline.insert_text(current_entry)
        readline.redisplay()

    readline.set_pre_input_hook(pre_input_hook)
    try:
        new_entry = input("Edit entry: ")
        return new_entry.strip() if new_entry.strip() else None
    finally:
        readline.set_pre_input_hook(None)


def _update_display_and_refresh(
    live, commit, i, total, should_thank, is_discarded, feedback_message
):
    """Helper to update display and refresh - reduces repetition."""
    display_panel = _create_commit_display(
        commit, i, total, should_thank, is_discarded, feedback_message
    )
    live.update(display_panel)
    live.refresh()


def _get_edited_prefix_interactive(current_prefix: Optional[str]) -> Optional[str]:
    """Get user's edited prefix with simple prompt."""
    current_text = current_prefix or ""

    def pre_input_hook():
        readline.insert_text(current_text)
        readline.redisplay()

    readline.set_pre_input_hook(pre_input_hook)
    try:
        new_prefix = input("Edit prefix (without brackets): ")
        return new_prefix.strip() if new_prefix.strip() else None
    finally:
        readline.set_pre_input_hook(None)


def _guess_category(commit: ParsedCommit) -> str:
    """Simple category detection based on common keywords."""
    text = (commit.raw_changelog_entry or commit.raw_title).lower()

    # Check for documentation keywords
    if any(word in text for word in ["doc", "guide", "tutorial"]):
        return "Documentation"

    # Check for bugfix keywords
    if any(word in text for word in ["fix", "bug", "resolved"]):
        return "Bugfixes"

    # Check for Dagster Plus (internal repo only)
    internal_repo_name = str(INTERNAL_REPO.git_dir).split("/")[-2]
    if commit.repo_name == internal_repo_name:
        return "Dagster Plus"

    # Default to New
    return "New"


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

    # All commits already have categories assigned by _get_parsed_commit
    processed_commits = all_commits

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

    if not processed_commits or not current_commit:
        return "No commits to process."

    # Initial setup for first commit
    github_username = _extract_github_username(current_commit)
    is_external = not any(
        domain in current_commit.author_email for domain in ["elementl.com", "dagsterlabs.com"]
    )
    should_thank = bool(github_username and is_external)
    is_discarded = not current_commit.raw_changelog_entry
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
                is_discarded = not commit.raw_changelog_entry
                feedback_message = ""

                # Update display for current commit
                _update_display_and_refresh(
                    live,
                    commit,
                    i,
                    len(processed_commits),
                    should_thank,
                    is_discarded,
                    feedback_message,
                )

                while True:  # Allow multiple edits to same commit
                    try:
                        # Get single character input without Enter
                        old_settings = termios.tcgetattr(sys.stdin)
                        try:
                            tty.setraw(sys.stdin.fileno())
                            action = sys.stdin.read(1).lower()
                        finally:
                            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

                        # Handle escape sequences (arrow keys) - ignore them
                        if ord(action) == 27:  # ESC sequence
                            try:
                                sys.stdin.read(2)  # Discard the rest of the sequence
                            except Exception:
                                pass
                            continue

                        # Handle Enter key (carriage return)
                        if ord(action) == 13 or ord(action) == 10:
                            action = "accept"

                        if action in ("a", "accept") or ord(action) in (13, 10):
                            # Check if commit is undocumented and not discarded
                            is_undocumented = (
                                not commit.raw_changelog_entry
                                or commit.raw_changelog_entry == "<UNDOCUMENTED>"
                            )
                            if is_undocumented and not is_discarded:
                                feedback_message = "❌ Cannot accept undocumented commit. Please add changelog entry first or discard it."
                                _update_display_and_refresh(
                                    live,
                                    commit,
                                    i,
                                    len(processed_commits),
                                    should_thank,
                                    is_discarded,
                                    feedback_message,
                                )
                                # Continue loop to show same commit
                            elif not is_discarded:
                                # Add to changelog
                                final_commit = commit._replace(
                                    ignore=not should_thank
                                )  # Use ignore field to track thanks
                                final_commits.append(final_commit)
                                feedback_message = "✅ Added to changelog"
                                _update_display_and_refresh(
                                    live,
                                    commit,
                                    i,
                                    len(processed_commits),
                                    should_thank,
                                    is_discarded,
                                    feedback_message,
                                )
                                i += 1  # Move to next commit
                                break
                            else:
                                # Skip this commit
                                feedback_message = "⏭️ Skipped"
                                _update_display_and_refresh(
                                    live,
                                    commit,
                                    i,
                                    len(processed_commits),
                                    should_thank,
                                    is_discarded,
                                    feedback_message,
                                )
                                i += 1  # Move to next commit
                                break

                        elif action == "c":
                            # Cycle category
                            internal_repo_name = str(INTERNAL_REPO.git_dir).split("/")[-2]
                            is_internal = commit.repo_name == internal_repo_name
                            new_category = _cycle_category(commit.changelog_category, is_internal)

                            commit = commit._replace(changelog_category=new_category, ignore=False)
                            # Update the commit in the processed_commits list
                            processed_commits[i - 1] = commit
                            feedback_message = f"✅ Category cycled to {new_category}"

                            # Update display with new category
                            _update_display_and_refresh(
                                live,
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
                            # Continue loop to show updated commit

                        elif action == "p":
                            # Edit prefix with simple prompt
                            live.stop()
                            console.clear()
                            console.print(
                                f"\n[bold cyan]Editing Prefix for Commit {i}/{len(processed_commits)}[/bold cyan]"
                            )
                            console.print(f"Current: {commit.prefix or '(none)'}")
                            console.print()

                            new_prefix = _get_edited_prefix_interactive(commit.prefix)
                            if new_prefix != commit.prefix:
                                commit = commit._replace(prefix=new_prefix, ignore=False)
                                processed_commits[i - 1] = commit
                                prefix_display = new_prefix or "(none)"
                                feedback_message = f"✅ Prefix changed to {prefix_display}"
                            else:
                                feedback_message = (
                                    "Prefix edit cancelled"
                                    if new_prefix is None
                                    else "No changes made"
                                )

                            live.start()
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

                        elif action == "e":
                            # Edit text with simple prompt
                            live.stop()
                            console.clear()
                            console.print(
                                f"\n[bold cyan]Editing Entry for Commit {i}/{len(processed_commits)}[/bold cyan]"
                            )
                            console.print(
                                f"Current: {commit.raw_changelog_entry or commit.raw_title}"
                            )
                            console.print()

                            new_entry = _get_edited_entry_interactive(
                                commit.raw_changelog_entry or commit.raw_title
                            )
                            if new_entry and new_entry != (
                                commit.raw_changelog_entry or commit.raw_title
                            ):
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
                                processed_commits[i - 1] = commit
                                feedback_message = "✅ Text updated"
                            else:
                                feedback_message = (
                                    "Text edit cancelled" if not new_entry else "No changes made"
                                )

                            live.start()
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

                        elif action == "t":
                            # Toggle thanks
                            should_thank = not should_thank
                            status = "ON" if should_thank else "OFF"
                            feedback_message = f"✅ Thanks toggled {status}"
                            # Update display with new thanks status
                            _update_display_and_refresh(
                                live,
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
                            # Continue loop to show updated commit

                        elif action == "d":
                            # Toggle discard state
                            is_discarded = not is_discarded
                            if is_discarded:
                                feedback_message = "🚫 Toggled to discard mode"
                            else:
                                feedback_message = "✅ Toggled out of discard mode"
                            # Update display with new discard status
                            _update_display_and_refresh(
                                live,
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
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
                            _update_display_and_refresh(
                                live,
                                commit,
                                i,
                                len(processed_commits),
                                should_thank,
                                is_discarded,
                                feedback_message,
                            )
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
            "\n\n⚠️  Interrupted by user. Discarding all changes...",
            style="yellow",
        )
        return "No changelog generated - operation cancelled."

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
        grouped_commits[commit.changelog_category].append(commit)

    documented_text = ""

    for category in CATEGORY_ORDER:
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
    loading_text = Text("Setting up branches and parsing commits...", style="bold blue")
    with Live(loading_text, auto_refresh=True, refresh_per_second=4, console=console) as live:
        # ensure that the release branches are available locally
        for repo in [OSS_REPO, INTERNAL_REPO]:
            live.update(
                Text(
                    f"Checking out branches for {str(repo.git_dir).split('/')[-2]}...",
                    style="bold blue",
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
    try:
        new_text = _interactive_changelog_generation(new_version, prev_version)

        # Only write if generation was successful (not cancelled)
        if new_text and not new_text.startswith("No changelog generated"):
            with open(CHANGELOG_PATH) as f:
                current_changelog = f.read()

            new_changelog = new_text + current_changelog[1:]

            with open(CHANGELOG_PATH, "w") as f:
                f.write(new_changelog)

            console.print("\n🎉 Interactive changelog generation complete!", style="bold green")
            console.print(f"📝 Changelog updated in {CHANGELOG_PATH}")
        else:
            console.print("\n⚠️  Changelog generation cancelled - no changes made.", style="yellow")
    except KeyboardInterrupt:
        console.print(
            "\n\n⚠️  Operation cancelled by user - no changes made to changelog.", style="yellow"
        )


if __name__ == "__main__":
    generate_changelog()
