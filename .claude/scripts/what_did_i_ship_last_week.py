#!/usr/bin/env python3
"""What Did I Ship Last Week - Generate impact-focused commit report.

Usage: python what_did_i_ship_last_week.py

This script has opinionated defaults:
- Always uses current git user's email
- Always searches dagster, internal, dagster-compass repos
- Always generates detailed impact-focused reports
- Always uploads to GitHub Gist
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import NamedTuple, Optional

import click

try:
    from anthropic import Anthropic
except ImportError:
    click.echo(
        "❌ Error: anthropic package not installed. Please install with: pip install anthropic"
    )
    sys.exit(1)


class PRInfo(NamedTuple):
    number: int
    title: str
    comments: int = 0
    reviews: int = 0
    review_comments: int = 0
    url: str = ""
    comment_bodies: list[str] = []
    review_bodies: list[str] = []

    @property
    def has_significant_discussion(self) -> bool:
        """Check if PR had significant discussion based on comment/review counts."""
        return self.comments >= 5 or self.review_comments >= 10 or self.reviews >= 3

    def _clean_comment_text(self, text: str) -> str:
        """Clean comment text by removing HTML, links, and other noise while preserving usernames."""
        import re

        # Store original text for username preservation
        original_text = text

        # Remove HTML tags but preserve content
        text = re.sub(r"<[^>]+>", "", text)

        # Remove Graphite navigation elements and links
        text = re.sub(r'\* \*\*#\d+\*\* <a href="https://app\.graphite\.dev[^>]*>.*?</a>', "", text)
        text = re.sub(r"\* \*\*#\d+\*\*[^*]*👈[^*]*\(View in Graphite\)", "", text)
        text = re.sub(r"\* \*\*#\d+\*\*[^-]*---", "", text)
        text = re.sub(r"👈[^)]*\(View in Graphite\)", "", text)

        # Remove Graphite stack navigation patterns
        text = re.sub(r"\* \*\*#\d+\*\* : \d+ [^(]*\(#\d+[^)]*\)", "", text)
        text = re.sub(r"\* \*\*#\d+\*\*[^*]*\* \*\*#\d+\*\*", "", text)
        text = re.sub(r"\* `master`", "", text)

        # Remove URLs but preserve @ mentions
        text = re.sub(r"https?://[^\s]+", "", text)

        # Remove common bot/automation text
        text = re.sub(
            r"This stack of pull requests is managed by Graphite.*", "", text, flags=re.IGNORECASE
        )
        text = re.sub(r"### Merge activity.*", "", text, flags=re.IGNORECASE)

        # Remove deploy preview and CI notifications
        text = re.sub(r"Deploy preview.*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Build succeeded.*", "", text, flags=re.IGNORECASE)

        # Extract and preserve usernames from original text
        usernames = re.findall(r"@\w+", original_text)

        # Remove excessive whitespace and newlines
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n+", "\n", text)
        text = re.sub(r"^\s*---\s*", "", text)
        text = re.sub(r"\s*---\s*$", "", text)

        # Re-insert important usernames if they were lost
        cleaned = text.strip()
        if usernames and cleaned and not any(username in cleaned for username in usernames):
            # If we lost all usernames, try to preserve context by prefixing with the first one
            cleaned = f"{usernames[0]}: {cleaned}"

        return cleaned

    @property
    def discussion_summary(self) -> str:
        """Get cleaned discussion content for AI analysis."""
        all_comments = self.comment_bodies + self.review_bodies
        if not all_comments:
            return ""

        # Clean each comment and filter out very short ones
        cleaned_comments = []
        for comment in all_comments:
            cleaned = self._clean_comment_text(comment)
            # Only include comments with substantial content (>20 chars after cleaning)
            if len(cleaned) > 20:
                cleaned_comments.append(cleaned)

        # Join meaningful comments
        return "\n\n---\n\n".join(cleaned_comments)


class CommitInfo(NamedTuple):
    sha: str
    message: str
    date: str
    author: str
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0
    pr_info: Optional[PRInfo] = None


class RepoStats(NamedTuple):
    name: str
    commits: list[CommitInfo]
    total_additions: int
    total_deletions: int
    total_files: int


def run_command(
    cmd: list[str], capture_output: bool = True, cwd: Optional[str] = None
) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        return subprocess.run(
            cmd, capture_output=capture_output, text=True, cwd=cwd, timeout=30, check=False
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 1, "", "Command timed out")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def check_gh_auth() -> bool:
    """Check if GitHub CLI is authenticated."""
    result = run_command(["gh", "auth", "status"])
    return result.returncode == 0


def get_git_author() -> str:
    """Get the current git user email."""
    result = run_command(["git", "config", "user.email"])
    if result.returncode == 0:
        return result.stdout.strip()
    return os.getenv("USER", "unknown")


def extract_pr_number(commit_message: str) -> Optional[int]:
    """Extract PR number from commit message."""
    # Look for patterns like "(#1234)" or "PR #1234"
    patterns = [r"\(#(\d+)\)", r"PR #(\d+)", r"Pull request #(\d+)"]
    for pattern in patterns:
        match = re.search(pattern, commit_message)
        if match:
            return int(match.group(1))
    return None


def fetch_pr_details(repo: str, pr_number: int) -> Optional[PRInfo]:
    """Fetch detailed PR information including comments and reviews."""
    full_repo = f"dagster-io/{repo}"

    try:
        # Get basic PR info
        pr_cmd = ["gh", "api", f"repos/{full_repo}/pulls/{pr_number}"]
        pr_result = run_command(pr_cmd)

        if pr_result.returncode != 0:
            return None

        pr_data = json.loads(pr_result.stdout)

        # Get PR comments
        comments_cmd = ["gh", "api", f"repos/{full_repo}/issues/{pr_number}/comments", "--paginate"]
        comments_result = run_command(comments_cmd)

        comment_bodies = []
        if comments_result.returncode == 0:
            try:
                comments_data = json.loads(comments_result.stdout)
                comment_bodies = [
                    comment.get("body", "") for comment in comments_data if comment.get("body")
                ]
            except json.JSONDecodeError:
                pass

        # Get PR review comments
        review_comments_cmd = [
            "gh",
            "api",
            f"repos/{full_repo}/pulls/{pr_number}/comments",
            "--paginate",
        ]
        review_comments_result = run_command(review_comments_cmd)

        # Get PR reviews
        reviews_cmd = ["gh", "api", f"repos/{full_repo}/pulls/{pr_number}/reviews", "--paginate"]
        reviews_result = run_command(reviews_cmd)

        review_bodies = []
        review_count = 0
        review_comment_count = 0

        if reviews_result.returncode == 0:
            try:
                reviews_data = json.loads(reviews_result.stdout)
                review_count = len(reviews_data)
                review_bodies = [
                    review.get("body", "") for review in reviews_data if review.get("body")
                ]
            except json.JSONDecodeError:
                pass

        if review_comments_result.returncode == 0:
            try:
                review_comments_data = json.loads(review_comments_result.stdout)
                review_comment_count = len(review_comments_data)
                # Add review comment bodies to review_bodies
                review_bodies.extend(
                    [rc.get("body", "") for rc in review_comments_data if rc.get("body")]
                )
            except json.JSONDecodeError:
                pass

        return PRInfo(
            number=pr_number,
            title=pr_data.get("title", ""),
            comments=len(comment_bodies),
            reviews=review_count,
            review_comments=review_comment_count,
            url=pr_data.get("html_url", ""),
            comment_bodies=comment_bodies,
            review_bodies=review_bodies,
        )

    except (json.JSONDecodeError, Exception):
        return None


def calculate_previous_week() -> tuple[datetime, datetime]:
    """Calculate the start and end times for the previous week.

    Previous week = Monday 12:01 AM to Sunday 11:59 PM of the week before this one.
    """
    now = datetime.now()
    current_dow = now.weekday()  # 0=Monday, 6=Sunday

    # Calculate days back to get to Monday of previous week
    # If today is Monday (0), we want to go back 7 days to last Monday
    # If today is Tuesday (1), we want to go back 8 days to last Monday
    # etc.
    days_back_to_prev_monday = current_dow + 7

    # Start of previous week Monday at 12:01 AM
    start_date = now - timedelta(days=days_back_to_prev_monday)
    start_time = start_date.replace(hour=0, minute=1, second=0, microsecond=0)

    # End of previous week Sunday at 11:59 PM
    end_date = start_date + timedelta(days=6)  # 6 days after Monday = Sunday
    end_time = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    return start_time, end_time


def categorize_commit(message: str) -> str:
    """Categorize a commit based on its message."""
    message_lower = message.lower()

    categories = [
        ("🚀 Features", ["feat", "feature", "add", "implement"]),
        ("🐛 Bug Fixes", ["fix", "bug", "patch"]),
        ("📚 Documentation", ["doc", "readme", "comment"]),
        ("🧪 Testing", ["test", "spec"]),
        ("♻️ Refactoring", ["refactor", "clean", "reorganize"]),
        ("⚙️ CI/CD", ["ci", "build", "deploy"]),
        ("⚡ Performance", ["perf", "optimize", "performance"]),
        ("🔒 Security", ["security", "auth", "permission"]),
    ]

    for category, keywords in categories:
        if any(keyword in message_lower for keyword in keywords):
            return category

    return "🔧 Other"


def get_local_commits(
    author_email: str, start_time: datetime, end_time: datetime
) -> list[CommitInfo]:
    """Get commits from local git repository."""
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

    cmd = [
        "git",
        "log",
        f"--author={author_email}",
        f"--since={start_str}",
        f"--until={end_str}",
        "--pretty=format:%H|%s|%ai|%an|%ae",
        "--shortstat",
    ]

    result = run_command(cmd)
    if result.returncode != 0:
        return []

    commits = []
    lines = result.stdout.strip().split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "|" in line:  # Commit line
            parts = line.split("|", 4)
            if len(parts) >= 5:
                sha, message, date, author_name, author_email = parts

                # Look for stats on next line
                additions, deletions, files_changed = 0, 0, 0
                if i + 1 < len(lines) and (
                    "insertion" in lines[i + 1] or "deletion" in lines[i + 1]
                ):
                    stats_line = lines[i + 1]
                    # Parse "X files changed, Y insertions(+), Z deletions(-)"
                    if "file" in stats_line:
                        parts = stats_line.split(",")
                        for part in parts:
                            part_stripped = part.strip()
                            if "file" in part_stripped:
                                files_changed = int(part_stripped.split()[0])
                            elif "insertion" in part_stripped:
                                additions = int(part_stripped.split()[0])
                            elif "deletion" in part_stripped:
                                deletions = int(part_stripped.split()[0])
                    i += 1  # Skip stats line

                # Extract PR number and fetch PR details
                pr_info = None
                pr_number = extract_pr_number(message.strip())
                if pr_number:
                    # For local commits, we assume we're in the dagster repo
                    pr_info = fetch_pr_details("dagster", pr_number)

                commits.append(
                    CommitInfo(
                        sha=sha.strip(),
                        message=message.strip(),
                        date=date.strip(),
                        author=author_name.strip(),
                        additions=additions,
                        deletions=deletions,
                        files_changed=files_changed,
                        pr_info=pr_info,
                    )
                )
        i += 1

    return commits


def get_github_commits(
    repo: str, author_email: str, start_time: datetime, end_time: datetime
) -> list[CommitInfo]:
    """Get commits from GitHub API using email-based search for accuracy."""
    # Use broader date range to account for timezone issues, then filter in code
    search_start = start_time - timedelta(days=1)  # Start a day earlier
    search_end = end_time + timedelta(days=1)  # End a day later

    start_iso = search_start.strftime("%Y-%m-%dT%H:%M:%S")
    end_iso = search_end.strftime("%Y-%m-%dT%H:%M:%S")

    full_repo = f"dagster-io/{repo}"

    # Search by email address which is much more reliable than username-based search
    cmd = [
        "gh",
        "search",
        "commits",
        f"--repo={full_repo}",
        f"--author-email={author_email}",
        f"--author-date={start_iso}..{end_iso}",
        "--json=sha,commit,author",
        "--limit=100",
    ]

    result = run_command(cmd)
    if result.returncode != 0:
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    commits = []
    for item in data:
        sha = item.get("sha", "")
        commit_data = item.get("commit", {})
        message = commit_data.get("message", "")
        date = commit_data.get("author", {}).get("date", "")
        author_name = commit_data.get("author", {}).get("name", "")
        commit_author_email = commit_data.get("author", {}).get("email", "")

        # Filter by exact email match (since we used broader date range)
        if commit_author_email.lower() != author_email.lower():
            continue

        # Parse commit date and check if it's in our actual date range
        try:
            commit_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
            # Convert to local time for comparison (approximate)
            commit_date_local = commit_date.replace(tzinfo=None)
            if not (start_time <= commit_date_local <= end_time):
                continue
        except (ValueError, TypeError):
            # If we can't parse date, include it to be safe
            pass

        # Get detailed stats for each commit
        stats_cmd = ["gh", "api", f"repos/{full_repo}/commits/{sha}"]
        stats_result = run_command(stats_cmd)

        additions, deletions, files_changed = 0, 0, 0
        if stats_result.returncode == 0:
            try:
                stats_data = json.loads(stats_result.stdout)
                stats = stats_data.get("stats", {})
                additions = stats.get("additions", 0)
                deletions = stats.get("deletions", 0)
                files_changed = len(stats_data.get("files", []))
            except (json.JSONDecodeError, KeyError):
                pass

        # Extract PR number and fetch PR details
        pr_info = None
        pr_number = extract_pr_number(message)
        if pr_number:
            pr_info = fetch_pr_details(repo, pr_number)

        commits.append(
            CommitInfo(
                sha=sha,
                message=message,
                date=date,
                author=author_name,
                additions=additions,
                deletions=deletions,
                files_changed=files_changed,
                pr_info=pr_info,
            )
        )

    return commits


def fetch_repo_commits(
    repo: str, author_email: str, start_time: datetime, end_time: datetime, use_local: bool = False
) -> RepoStats:
    """Fetch commits for a single repository."""
    click.echo(f"📊 Querying {repo}...")
    if use_local and repo == "dagster":
        commits = get_local_commits(author_email, start_time, end_time)
    else:
        commits = get_github_commits(repo, author_email, start_time, end_time)

    click.echo(f"   Found {len(commits)} commits")

    total_additions = sum(c.additions for c in commits)
    total_deletions = sum(c.deletions for c in commits)
    total_files = sum(c.files_changed for c in commits)

    return RepoStats(
        name=repo,
        commits=commits,
        total_additions=total_additions,
        total_deletions=total_deletions,
        total_files=total_files,
    )


def generate_repo_section(repo_stats: RepoStats, format_type: str) -> str:
    """Generate markdown section for a repository."""
    if not repo_stats.commits:
        return f"\n## dagster-io/{repo_stats.name}\nNo commits found.\n"

    output = []
    output.append(f"\n## dagster-io/{repo_stats.name} ({len(repo_stats.commits)} commits)\n")

    # Group commits by category
    categories = {}
    for commit in repo_stats.commits:
        category = categorize_commit(commit.message)
        if category not in categories:
            categories[category] = []
        categories[category].append(commit)

    # Show commits by category
    for category, commits in categories.items():
        if format_type == "brief" and len(output) > 10:  # Limit in brief mode
            break

        for commit in commits[: 5 if format_type == "brief" else None]:  # Top 5 in brief mode
            # Truncate long commit messages
            message = commit.message.split("\n")[0]  # First line only
            if len(message) > 80:
                message = message[:77] + "..."

            output.append(f"### {category}: {message}")
            output.append(f"- **Commit**: `{commit.sha[:7]}` - {commit.message.split(chr(10))[0]}")
            output.append(
                f"- **Files**: {commit.files_changed} changed (+{commit.additions} -{commit.deletions})"
            )

            # Format date
            try:
                date_obj = datetime.fromisoformat(commit.date.replace("Z", "+00:00"))
                formatted_date = date_obj.strftime("%B %d, %I:%M %p")
            except (ValueError, TypeError):
                formatted_date = commit.date
            output.append(f"- **Date**: {formatted_date}")

            # Try to extract PR number
            if "(#" in commit.message:
                pr_match = re.search(r"\(#(\d+)\)", commit.message)
                if pr_match:
                    output.append(f"- **PR**: #{pr_match.group(1)}")

            output.append("")

    output.append(
        f"**Repository Summary**: +{repo_stats.total_additions} -{repo_stats.total_deletions} across {repo_stats.total_files} files"
    )

    return "\n".join(output)


def format_commits_for_analysis(repo_stats_list: list[RepoStats]) -> str:
    """Format commit data for AI analysis."""
    output = []
    output.append("# COMMIT DATA FOR ANALYSIS")
    output.append("")

    for repo_stats in repo_stats_list:
        if not repo_stats.commits:
            continue

        output.append(f"## Repository: {repo_stats.name}")
        output.append(
            f"**Total Stats**: {len(repo_stats.commits)} commits, +{repo_stats.total_additions:,} -{repo_stats.total_deletions:,} lines, {repo_stats.total_files} files changed"
        )
        output.append("")

        for commit in repo_stats.commits:
            output.append(f"**{commit.sha[:7]}**: {commit.message.split(chr(10))[0]}")
            output.append(
                f"  - Files: {commit.files_changed}, +{commit.additions} -{commit.deletions}"
            )
            output.append(f"  - Date: {commit.date}")

            # Include PR information if available
            if commit.pr_info:
                pr = commit.pr_info
                output.append(f"  - PR #{pr.number}: {pr.title}")
                output.append(
                    f"  - Discussion: {pr.comments} comments, {pr.reviews} reviews, {pr.review_comments} review comments"
                )
                if pr.has_significant_discussion:
                    output.append("  - [SIGNIFICANT DISCUSSION]")
                if pr.discussion_summary:
                    output.append(f"  - Discussion content: {pr.discussion_summary}")

            if len(commit.message.split("\n")) > 1:
                # Show additional lines if present
                additional_lines = commit.message.split("\n")[1:3]  # Show up to 2 more lines
                for line in additional_lines:
                    if line.strip():
                        output.append(f"  - {line.strip()}")
            output.append("")

        output.append("")

    return "\n".join(output)


def generate_ai_analyzed_report(
    repo_stats_list: list[RepoStats],
    author: str,
    start_time: datetime,
    end_time: datetime,
) -> str:
    """Generate an AI-analyzed report using template prompts to drive analysis behavior."""
    # Define AI analysis prompt directly
    impact_prompt = """
You are analyzing commit data from Dagster repositories to generate an accurate technical impact summary. Your goal is to honestly categorize work and avoid inflating routine fixes into strategic achievements.

ANALYSIS APPROACH:
1. **Accurate Categorization**: Distinguish between new features, bug fixes, routine maintenance, and refactoring
2. **Honest Assessment**: Don't overstate the impact of small fixes or routine changes
3. **Technical Accuracy**: Use actual commit messages to determine if something is a fix vs feature
4. **Concrete Details**: Use actual commit messages, line counts, and specific changes

OUTPUT FORMAT:
### `repository-name` (X commits)
- **Features**: New capabilities or functionality added
- **Bug Fixes**: Issues resolved, broken functionality repaired
- **Refactoring/Maintenance**: Code improvements, reorganization, routine updates
- **Scale**: Lines changed, files affected for significant work only
- **Key PRs**: [#1234](https://github.com/dagster-io/repo-name/pull/1234), [#5678](https://github.com/dagster-io/repo-name/pull/5678) for significant groups of related work

CATEGORIZATION GUIDELINES:
- **Bug Fix indicators**: "Fix", "Resolve", "Correct", "Repair", "Handle", missing methods/functionality
- **Feature indicators**: "Add", "Implement", "Create", "Enable", "Support", new capabilities
- **Refactoring indicators**: "Extract", "Refactor", "Reorganize", "Consolidate", "Move", "Split"
- **Maintenance indicators**: "Update", "Bump", "Clean", "Remove", "Delete", dependency updates

AVOID:
- Calling bug fixes "enhancements" or "improvements" 
- Inflating routine maintenance as strategic work
- Using marketing language for technical fixes
- Overstating the impact of small changes
- Mentioning formatting changes, linting fixes, or code style updates

PR LINK FORMATTING:
- Use the provided PR information from the commit data (PR numbers, titles, comment counts are already fetched)
- Format as clickable links: [#1234](https://github.com/dagster-io/repository-name/pull/1234)  
- Use actual repository name (dagster, internal, dagster-compass)
- Flag PRs marked with "[SIGNIFICANT DISCUSSION]" in the data with 💬: [#1234 💬](https://github.com/dagster-io/repository-name/pull/1234)
- Incorporate actual discussion content when analyzing the impact and context of changes
- Only include PRs for significant work, not every minor commit
- Group related PRs together under appropriate categories

CODE FORMATTING:
- Surround function names with backticks: `get_records_for_run`, `report_runless_asset_event`
- Surround class names with backticks: `FreshnessStateChange`, `DagsterInstance`, `AssetDomain`
- Surround module names with backticks: `dagster_instance.py`, `asset_domain.py`

DISCUSSION ANALYSIS:
- Use actual PR discussion data provided in the commit information
- PRs marked with "[SIGNIFICANT DISCUSSION]" had extensive comments, reviews, or discussions
- Review the "Discussion content" field to understand the nature of conversations and feedback
- Consider discussion context when describing the impact and collaborative aspects of the work
- Use comment content to identify design decisions, trade-offs, and technical considerations discussed

EXAMPLES:
❌ "Datadog Integration Improvements: Added granular run record tracking for enhanced observability"
✅ "Bug Fix: Add missing `get_records_for_run` method to fix Datadog tracing integration"

❌ "Enhanced CI/CD Intelligence System with automated failure analysis"  
✅ "Feature: Add buildkite-error-detective agent for automated CI failure analysis"

❌ "Fix report_runless_asset_event to accept FreshnessStateChange events"
✅ "Bug Fix: Fix `report_runless_asset_event` to accept `FreshnessStateChange` events"

❌ "Key PRs: [#1234](https://github.com/dagster-io/dagster/pull/1234)"
✅ "Key PRs: [#1234 💬](https://github.com/dagster-io/dagster/pull/1234)" (for PRs with significant discussion indicators)
"""

    # Format commit data for AI analysis
    commit_data = format_commits_for_analysis(repo_stats_list)

    # Calculate totals
    total_commits = sum(len(rs.commits) for rs in repo_stats_list)
    active_repos = sum(1 for rs in repo_stats_list if rs.commits)
    total_additions = sum(rs.total_additions for rs in repo_stats_list)
    total_deletions = sum(rs.total_deletions for rs in repo_stats_list)
    total_files = sum(rs.total_files for rs in repo_stats_list)

    if total_commits == 0:
        return "# Weekly Shipping Report\n\nNo commits found for the specified period."

    # Use AI to analyze different sections
    click.echo("🤖 Using AI to analyze commit impact...")

    # Perform AI analysis using the hardcoded prompt and commit data
    impact_analysis = analyze_with_ai("Impact Summary", impact_prompt, commit_data)

    # Generate report structure
    output = []

    # Header
    output.append("# Weekly Shipping Report")
    output.append("")
    output.append(f"**Author**: {author}")
    start_str = start_time.strftime("%A, %B %d, %Y %I:%M %p")
    end_str = end_time.strftime("%A, %B %d, %Y %I:%M %p")
    output.append(f"**Period**: {start_str} - {end_str}")
    output.append("")

    # AI-generated sections
    output.append("## Impact Summary")
    output.append("")
    output.append(impact_analysis if impact_analysis else "*Unable to generate AI analysis*")
    output.append("")

    # Rest of report (unchanged)
    output.append("---")
    output.append("")
    output.append("## Appendix")
    output.append("")

    # Weekly Statistics
    output.append("### Weekly Statistics")
    output.append(f"- **Total Commits**: {total_commits}")
    output.append(f"- **Active Repositories**: {active_repos}")
    output.append(f"- **Files Changed**: {total_files}")
    output.append(f"- **Lines Added**: {total_additions:,}")
    output.append(f"- **Lines Removed**: {total_deletions:,}")
    output.append("- **Report Format**: detailed")

    avg_commits = total_commits / 7
    output.append(f"- **Average commits per day**: {avg_commits:.1f}")

    # Most active repository
    most_active = max(repo_stats_list, key=lambda rs: len(rs.commits))
    if most_active.commits:
        output.append(
            f"- **Most active repository**: {most_active.name} ({len(most_active.commits)} commits)"
        )

    output.append(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("")

    # All Commits
    output.append("### All Commits")
    output.append("")

    for repo_stats in repo_stats_list:
        if repo_stats.commits:
            output.append(f"#### dagster-io/{repo_stats.name} ({len(repo_stats.commits)} commits)")
            output.append("")

            for commit in repo_stats.commits:
                # Extract PR number and create link
                pr_number = extract_pr_number(commit.message)

                # Format date simply
                try:
                    date_obj = datetime.fromisoformat(commit.date.replace("Z", "+00:00"))
                    simple_date = date_obj.strftime("%b %d")
                except (ValueError, TypeError):
                    simple_date = commit.date[:10] if len(commit.date) >= 10 else commit.date

                # Get clean commit message (remove PR references)
                clean_message = commit.message.split(chr(10))[0]
                # Remove PR references from end of message like "(#31502) (#31502)"
                clean_message = re.sub(r"\s*\(#\d+\)(\s*\(#\d+\))*\s*$", "", clean_message)

                # Format as PR-centric: * (#PR) Title - Date
                if pr_number:
                    discussion_flag = ""
                    if commit.pr_info and commit.pr_info.has_significant_discussion:
                        discussion_flag = " 💬"
                    pr_url = f"https://github.com/dagster-io/{repo_stats.name}/pull/{pr_number}"
                    output.append(
                        f"* ([#{pr_number}{discussion_flag}]({pr_url})) {clean_message} - {simple_date}"
                    )

                    # Add AI-generated discussion summary as subbullets if PR had significant discussion
                    if (
                        commit.pr_info
                        and commit.pr_info.has_significant_discussion
                        and commit.pr_info.discussion_summary
                    ):
                        # Generate AI summary of discussion
                        discussion_bullets = analyze_pr_discussion(
                            commit.pr_info.discussion_summary
                        )
                        if discussion_bullets:
                            for bullet in discussion_bullets:
                                output.append(f"  - {bullet}")
                else:
                    # For commits without PR, show commit hash
                    output.append(f"* **{commit.sha[:7]}** {clean_message} - {simple_date}")

            output.append("")
            output.append(
                f"**Repository Summary**: +{repo_stats.total_additions} -{repo_stats.total_deletions} across {repo_stats.total_files} files"
            )
            output.append("")

    output.append("---")
    output.append("*Report generated by Claude Code what_did_i_ship_last_week command*")

    return "\n".join(output)


def analyze_pr_discussion(discussion_content: str) -> list[str]:
    """Use AI to analyze PR discussion and generate concise bullet points."""
    if not discussion_content.strip():
        return []

    # Check for API key
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        return []

    try:
        client = Anthropic(api_key=anthropic_api_key)

        prompt = f"""
Analyze the following PR discussion content and create 2-5 concise bullet points that capture the key human-to-human technical discussions. PRIORITIZE:

1. WHO said WHAT - Always include participant names (e.g., "@OwenKephart suggested...", "Discussion between @schrockn and @reviewer about...")
2. Technical decisions and specific rationale provided by reviewers/contributors
3. Design alternatives proposed by specific people
4. Implementation concerns raised by named reviewers
5. Technical trade-offs debated between specific participants

IGNORE/DE-EMPHASIZE:
- Bot comments, automation messages, deploy notifications
- Generic process comments without specific technical content
- Simple approvals or administrative comments
- Graphite/CI automation responses

FORMAT: Include participant usernames when available. Focus on the human conversation and technical substance.
Each bullet should be 1-2 sentences maximum and clearly attribute ideas/feedback to specific people when possible.

EXAMPLE GOOD FORMAT:
- @OwenKephart recommended using super().xyz() instead of AssetMethods.xyz(self) for cleaner implementation
- @schrockn and @reviewer discussed MRO fragility concerns, leading to AssetMethods syntax decision

PR Discussion Content:
{discussion_content}

Return only the bullet points, one per line:"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )

        # Handle different response formats
        response_text = ""
        if hasattr(response.content[0], "text"):
            response_text = response.content[0].text.strip()
        else:
            response_text = str(response.content[0]).strip()

        if response_text:
            # Split into bullet points and clean
            bullets = [bullet.strip() for bullet in response_text.split("\n") if bullet.strip()]
            # Return max 5 bullets
            return bullets[:5]

    except Exception:
        # Silently fail and return empty list if AI analysis fails
        pass

    return []


def analyze_with_ai(section_name: str, prompt: str, commit_data: str) -> str:
    """Analyze commit data using Anthropic AI to generate meaningful insights."""
    if not prompt.strip():
        raise ValueError(f"No analysis prompt found for {section_name}")

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Create a detailed analysis prompt
    full_prompt = f"""
{prompt}

COMMIT DATA TO ANALYZE:
{commit_data}

Please analyze this commit data and generate a detailed {section_name} section. Focus on:
1. Specific technical achievements with actual commit details
2. Business impact and strategic value of the work
3. Concrete improvements rather than generic categories
4. Use the actual commit messages and statistics provided

CRITICAL: Completely ignore and do not mention:
- Formatting changes (yarn format, ruff format, etc.)  
- Linting fixes or code style updates
- Line length standardization
- Cosmetic code changes that don't add functionality
- Cross-repository coordination or synchronization

IMPORTANT: Use PR discussion content when available:
- Review comment content to understand design decisions and trade-offs
- Incorporate reviewer feedback context to explain why changes were made  
- Use discussion content to identify collaborative aspects and technical considerations
- Highlight PRs that had significant technical discussions affecting the implementation

Focus only on substantive technical work that adds business value or capabilities within each repository.

Provide a detailed, specific analysis that goes beyond simple categorization and incorporates discussion context where available.
"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        temperature=0.3,
        messages=[{"role": "user", "content": full_prompt}],
    )

    # Handle different response formats from anthropic library
    if hasattr(response.content[0], "text"):
        return response.content[0].text.strip()
    else:
        # Fallback for different response structure
        return str(response.content[0]).strip()


def upload_to_gist(content: str, filename: str = "weekly_shipping_report.md") -> Optional[str]:
    """Upload the report to a GitHub Gist."""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        cmd = ["gh", "gist", "create", temp_file, "--filename", filename]
        result = run_command(cmd)

        os.unlink(temp_file)  # Clean up temp file

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None

    except Exception:
        return None


@click.command()
def main():
    """Generate an impact-focused weekly shipping report and upload to GitHub Gist.

    Uses opinionated defaults:
    - Current git user's email for commit attribution
    - All Dagster repositories (dagster, internal, dagster-compass)
    - Detailed, impact-focused report format
    - Always uploads to GitHub Gist
    """
    # Check for required ANTHROPIC_API_KEY environment variable
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        click.echo("❌ Error: ANTHROPIC_API_KEY environment variable is required")
        click.echo("   This script uses AI analysis to generate meaningful weekly reports.")
        click.echo("   Please set your Anthropic API key:")
        click.echo("   export ANTHROPIC_API_KEY='your-api-key-here'")
        click.echo("")
        click.echo("   You can get an API key from: https://console.anthropic.com/")
        sys.exit(1)

    # Use opinionated defaults
    repos = "dagster,internal,dagster-compass"
    author_email = get_git_author()

    # Check GitHub CLI auth
    if not check_gh_auth():
        click.echo("❌ GitHub CLI not authenticated. Please run 'gh auth login'")
        sys.exit(1)

    # Calculate date range
    start_time, end_time = calculate_previous_week()

    click.echo(f"🔍 Generating report for {author_email} from {start_time} to {end_time}")

    # Parse repositories
    repo_list = [repo.strip() for repo in repos.split(",")]

    # Check if we're in a git repository for local optimization
    use_local = Path(".git").exists()

    # Fetch commits from all repositories in parallel
    click.echo("🚀 Fetching commit data from repositories...")
    repo_stats_list = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_repo = {
            executor.submit(
                fetch_repo_commits,
                repo,
                author_email,
                start_time,
                end_time,
                use_local and repo == "dagster",
            ): repo
            for repo in repo_list
        }

        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                repo_stats = future.result()
                repo_stats_list.append(repo_stats)
            except Exception:
                # Add empty stats to maintain repo order
                repo_stats_list.append(RepoStats(repo, [], 0, 0, 0))

    # Sort by original repo order
    repo_order = {repo: i for i, repo in enumerate(repo_list)}
    repo_stats_list.sort(key=lambda rs: repo_order.get(rs.name, 999))

    # Generate AI-analyzed report
    report = generate_ai_analyzed_report(repo_stats_list, author_email, start_time, end_time)

    # Display report
    click.echo("\n" + "=" * 80)
    click.echo(report)
    click.echo("=" * 80)

    # Always upload to gist (opinionated default)
    click.echo("\n📤 Uploading to GitHub Gist...")
    gist_url = upload_to_gist(report)
    if gist_url:
        click.echo(f"✅ Report uploaded to: {gist_url}")
    else:
        click.echo("❌ Failed to upload to gist")

    click.echo("\n✅ Report generated successfully!")


if __name__ == "__main__":
    main()
