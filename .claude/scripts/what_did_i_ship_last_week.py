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


class CommitInfo(NamedTuple):
    sha: str
    message: str
    date: str
    author: str
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0


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


def calculate_previous_week() -> tuple[datetime, datetime]:
    """Calculate the start and end times for the previous week."""
    now = datetime.now()
    current_dow = now.weekday()  # 0=Monday, 6=Sunday

    if current_dow == 6:  # Sunday
        days_back = 6
    elif current_dow == 0 and now.hour < 9:  # Monday before 9 AM
        days_back = 7
    else:
        days_back = current_dow + 6

    # Start of previous Monday at 9 AM
    start_date = now - timedelta(days=days_back)
    start_time = start_date.replace(hour=9, minute=0, second=0, microsecond=0)

    return start_time, now


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

                commits.append(
                    CommitInfo(
                        sha=sha.strip(),
                        message=message.strip(),
                        date=date.strip(),
                        author=author_name.strip(),
                        additions=additions,
                        deletions=deletions,
                        files_changed=files_changed,
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

        commits.append(
            CommitInfo(
                sha=sha,
                message=message,
                date=date,
                author=author_name,
                additions=additions,
                deletions=deletions,
                files_changed=files_changed,
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
You are analyzing commit data from Dagster repositories to generate a detailed technical impact summary. Your goal is to identify concrete business value and technical achievements rather than generic categorizations.

ANALYSIS APPROACH:
1. **Business Impact First**: What problems were solved? What capabilities were added?
2. **Technical Depth**: Specific technologies, patterns, architectures implemented
3. **Strategic Value**: How does this work enable future development or reduce friction?
4. **Concrete Details**: Use actual commit messages, line counts, and specific changes

OUTPUT FORMAT:
### `repository-name` (X commits)
- **Major Achievements**: 2-3 specific accomplishments with business context
- **Technical Implementation**: Key technologies/patterns used, architecture changes
- **Scale**: Lines changed, files affected, complexity indicators
- **Strategic Impact**: How this enables future work or solves persistent problems

FOCUS AREAS TO IDENTIFY:
- **Infrastructure Evolution**: Deployment, monitoring, scaling, reliability improvements
- **Developer Productivity**: Tooling, automation, workflow improvements that save time
- **Code Quality Systems**: Automated checks, standards, testing frameworks that prevent issues
- **API & Framework Evolution**: Breaking changes, new capabilities, developer experience improvements
- **System Architecture**: Storage layers, abstractions, performance optimizations

AVOID:
- Generic categories like "bug fixes" without context
- Simple keyword matching
- Vague descriptions like "various improvements"
- Listing commits without explaining their significance
- Mentioning formatting changes, linting fixes, or code style updates
- Discussing yarn format, ruff format, line length changes, or similar cosmetic changes

EXAMPLE QUALITY:
❌ "Infrastructure improvements (5 commits): Various deployment and CI changes"
✅ "Render Deployment Infrastructure: Implemented comprehensive health monitoring system with PostgreSQL/SQLite support, enabling reliable production deployments with automated failover and database migration capabilities (+847 lines, 12 files). This replaces manual deployment processes and provides foundation for multi-environment scaling."
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
                # Extract PR number if present
                pr_part = ""
                if "(#" in commit.message:
                    pr_match = re.search(r"\(#(\d+)\)", commit.message)
                    if pr_match:
                        pr_part = f" (#{pr_match.group(1)})"

                # Format date simply
                try:
                    date_obj = datetime.fromisoformat(commit.date.replace("Z", "+00:00"))
                    simple_date = date_obj.strftime("%b %d")
                except (ValueError, TypeError):
                    simple_date = commit.date[:10] if len(commit.date) >= 10 else commit.date

                # One line per commit
                output.append(
                    f"- **{commit.sha[:7]}** {commit.message.split(chr(10))[0]}{pr_part} - {simple_date}"
                )

            output.append("")
            output.append(
                f"**Repository Summary**: +{repo_stats.total_additions} -{repo_stats.total_deletions} across {repo_stats.total_files} files"
            )
            output.append("")

    output.append("---")
    output.append("*Report generated by Claude Code what_did_i_ship_last_week command*")

    return "\n".join(output)


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

Focus only on substantive technical work that adds business value or capabilities within each repository.

Provide a detailed, specific analysis that goes beyond simple categorization.
"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        temperature=0.3,
        messages=[{"role": "user", "content": full_prompt}],
    )

    return response.content[0].text.strip()


def upload_to_gist(content: str, filename: str = "weekly_shipping_report.md") -> Optional[str]:
    """Upload the report to a GitHub Gist."""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        cmd = ["gh", "gist", "create", temp_file, "--filename", filename, "--public"]
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
