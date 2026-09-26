#!/usr/bin/env python3
"""Claude Code status line prompt generator for dagster-dev."""

import json
import os
import re
import shutil
import subprocess
import sys
import traceback
from datetime import datetime

import click

# Enable debug mode by setting environment variable DEBUG_STATUSLINE=1
DEBUG = os.environ.get("DEBUG_STATUSLINE") == "1"


def debug_print(*args):
    """Print debug information to stderr if debug mode is enabled."""
    if DEBUG:
        click.echo(f"DEBUG: {' '.join(map(str, args))}", err=True)


def get_terminal_width():
    """Get terminal width with fallback."""
    try:
        return shutil.get_terminal_size().columns
    except OSError:
        return 80


def strip_ansi_length(text):
    """Calculate text length without ANSI escape sequences."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return len(ansi_escape.sub("", text))


def get_buildkite_status(cwd, branch):
    """Get Buildkite build status for the current branch."""
    try:
        os.chdir(cwd)
        debug_print(f"Getting Buildkite status for branch: {branch}")

        # Use dagster-dev to get latest build number for PR
        build_number_result = subprocess.run(
            ["dagster-dev", "bk-latest-build-for-pr"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        if build_number_result.returncode != 0:
            debug_print(f"dagster-dev bk-latest-build-for-pr failed: {build_number_result.stderr}")
            return ""

        build_number = build_number_result.stdout.strip()
        if not build_number:
            debug_print("No Buildkite build number found")
            return ""

        # Get build status using dagster-dev
        status_result = subprocess.run(
            ["dagster-dev", "bk-build-status", build_number, "--json"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        if status_result.returncode != 0:
            debug_print(f"dagster-dev bk-build-status failed: {status_result.stderr}")
            # Fallback to just showing build URL without status
            build_url = f"https://buildkite.com/dagster/dagster-dagster/builds/{build_number}"
            return f"⚪\u00a0{build_url}"

        # Parse JSON status
        status_data = json.loads(status_result.stdout)
        build_status = status_data.get("status", "unknown")

        # Determine status emoji
        if build_status == "passed":
            status_emoji = "✅"
        elif build_status == "failed":
            status_emoji = "❌"
        elif build_status == "running":
            status_emoji = "🏃‍♂️"
        else:
            status_emoji = "⚪"

        # Construct Buildkite URL
        build_url = f"https://buildkite.com/dagster/dagster-dagster/builds/{build_number}"
        debug_print(
            f"Found Buildkite build #{build_number} with status '{build_status}': {build_url}"
        )

        # Use non-breaking space to keep emoji and URL together
        return f"{status_emoji}\u00a0{build_url}"

    except Exception as e:
        debug_print(f"Error getting Buildkite status: {e}")
        return ""


def get_pr_status_emoji(cwd, branch):
    """Get PR status emoji based on GitHub PR state."""
    try:
        os.chdir(cwd)
        debug_print(f"Getting PR status for branch: {branch}")

        # Get PR status using GitHub CLI
        status_result = subprocess.run(
            [
                "gh",
                "pr",
                "view",
                branch,
                "--json",
                "mergeable,reviewDecision,mergeStateStatus,state,isDraft",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if status_result.returncode != 0:
            debug_print(f"gh pr view failed: {status_result.stderr}")
            return ""

        pr_data = json.loads(status_result.stdout)
        debug_print(f"PR status data: {pr_data}")

        mergeable = pr_data.get("mergeable", "")
        review_decision = pr_data.get("reviewDecision", "")
        merge_state_status = pr_data.get("mergeStateStatus", "")
        state = pr_data.get("state", "")
        is_draft = pr_data.get("isDraft", False)

        # PR is closed/merged
        if state != "OPEN":
            return ""

        # Priority order for status determination:
        # 1. Draft state (work in progress)
        if is_draft:
            debug_print("PR is in draft state")
            return "🚧"

        # 2. Merge conflicts (highest priority for non-draft)
        if mergeable == "CONFLICTING":
            debug_print("PR has merge conflicts")
            return "🔀"

        # 3. Changes requested
        if review_decision == "CHANGES_REQUESTED":
            debug_print("PR has changes requested")
            return "📝"

        # 4. Approved and ready to merge
        if review_decision == "APPROVED" and mergeable == "MERGEABLE":
            debug_print("PR is approved and ready to merge")
            return "✅"

        # 5. Blocked for other reasons
        if merge_state_status == "BLOCKED":
            debug_print("PR is blocked")
            return "🚫"

        # 6. Published but waiting for reviewers (default state)
        debug_print("PR is published and waiting for review")
        return "👀"

    except Exception as e:
        debug_print(f"Error getting PR status: {e}")
        return ""


def get_graphite_pr_url(cwd, branch):
    """Get Graphite PR URL for the current branch if it exists."""
    try:
        # Change to the working directory
        os.chdir(cwd)
        debug_print(f"Looking for Graphite PR for branch: {branch} in {cwd}")

        # Method 1: Try gt info for the current branch
        try:
            gt_info_result = subprocess.run(
                ["gt", "info", branch], capture_output=True, text=True, timeout=10, check=False
            )

            debug_print(f"gt info return code: {gt_info_result.returncode}")
            if gt_info_result.returncode == 0:
                info_output = gt_info_result.stdout
                debug_print(f"gt info output: {info_output}")

                # Look for PR number in gt info output
                # Look for patterns like "PR #31780" or "#31780" or "pull/31780"
                pr_patterns = [
                    r"(?:PR\s*)?#(\d+)",
                    r"pull/(\d+)",
                    r"github\.com/[^/]+/[^/]+/pull/(\d+)",
                    r"pr/(\d+)",
                ]

                for pattern in pr_patterns:
                    pr_match = re.search(pattern, info_output, re.IGNORECASE)
                    if pr_match:
                        pr_number = pr_match.group(1)
                        debug_print(
                            f"Found PR #{pr_number} for branch {branch} from gt info using pattern {pattern}"
                        )
                        return f"https://app.graphite.dev/github/pr/dagster-io/dagster/{pr_number}"
        except Exception as e:
            debug_print(f"gt info failed: {e}")

        # Method 2: Use GitHub CLI to get PR number, then construct Graphite URL
        try:
            gh_result = subprocess.run(
                ["gh", "pr", "view", branch, "--json", "number"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            debug_print(f"gh pr view return code: {gh_result.returncode}")
            if gh_result.returncode == 0:
                pr_data = json.loads(gh_result.stdout)
                pr_number = pr_data.get("number")
                if pr_number:
                    debug_print(f"Found PR #{pr_number} for branch {branch} from GitHub CLI")
                    return f"https://app.graphite.dev/github/pr/dagster-io/dagster/{pr_number}"
            else:
                debug_print(f"gh pr view stderr: {gh_result.stderr}")
        except Exception as e:
            debug_print(f"GitHub CLI approach failed: {e}")

        # Method 3: Use gt log to get PR information
        try:
            gt_result = subprocess.run(
                ["gt", "log", "--oneline", "--max-count=10"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            debug_print(f"gt log return code: {gt_result.returncode}")
            if gt_result.returncode == 0:
                lines = gt_result.stdout.strip().split("\n")
                debug_print(f"gt log output: {gt_result.stdout}")

                for line in lines:
                    # Look for the current branch in gt log output
                    if branch in line and "(#" in line:
                        # Extract PR number from format like "branch_name (#12345)"
                        pr_match = re.search(r"\(#(\d+)\)", line)
                        if pr_match:
                            pr_number = pr_match.group(1)
                            debug_print(f"Found PR #{pr_number} for branch {branch} from gt log")
                            return (
                                f"https://app.graphite.dev/github/pr/dagster-io/dagster/{pr_number}"
                            )
        except Exception as e:
            debug_print(f"gt log failed: {e}")

        # Method 4: Use gt status to get PR info
        try:
            gt_status_result = subprocess.run(
                ["gt", "status"], capture_output=True, text=True, timeout=10, check=False
            )

            debug_print(f"gt status return code: {gt_status_result.returncode}")
            if gt_status_result.returncode == 0:
                status_output = gt_status_result.stdout
                debug_print(f"gt status output: {status_output}")

                # Look for PR information in gt status output
                pr_match = re.search(rf"{re.escape(branch)}.*?#(\d+)", status_output)
                if pr_match:
                    pr_number = pr_match.group(1)
                    debug_print(f"Found PR #{pr_number} from gt status")
                    return f"https://app.graphite.dev/github/pr/dagster-io/dagster/{pr_number}"
        except Exception as e:
            debug_print(f"gt status failed: {e}")

        debug_print(f"No PR found for branch {branch} using any method")
        return ""

    except Exception as e:
        debug_print(f"Error getting Graphite PR URL: {e}")
        return ""


def get_git_info(cwd):
    """Get git repository information."""
    try:
        # Change to the working directory
        debug_print(f"Checking git info for directory: {cwd}")
        os.chdir(cwd)

        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            return "", ""

        # Get branch name
        try:
            branch_result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if branch_result.returncode == 0:
                branch = branch_result.stdout.strip()
            else:
                # Fallback to commit hash if detached HEAD
                hash_result = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                branch = hash_result.stdout.strip() if hash_result.returncode == 0 else "unknown"
        except subprocess.TimeoutExpired:
            branch = "timeout"

        # Check for uncommitted changes
        try:
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            has_changes = (
                bool(status_result.stdout.strip()) if status_result.returncode == 0 else False
            )
        except subprocess.TimeoutExpired:
            has_changes = False

        # Get Graphite PR URL
        pr_url = get_graphite_pr_url(cwd, branch)

        if has_changes:
            git_info = f" git:({branch}) ✗"
        else:
            git_info = f" git:({branch})"

        return git_info, pr_url

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
        return "", ""


def get_model_abbreviation(model_name):
    """Get model abbreviation."""
    if "Sonnet" in model_name:
        return "S"
    elif "Opus" in model_name:
        return "O"
    elif "Haiku" in model_name:
        return "H"
    else:
        return "?"


def count_tokens_precisely(text):
    """More precise token counting using word-based estimation."""
    # Split on whitespace and punctuation to get rough word count
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)

    # Count code tokens more precisely
    code_chars = len(re.findall(r"[{}()\[\];,.]", text))  # Structural code characters

    # Estimate tokens more precisely:
    # - Regular words: ~0.75 tokens per word (accounts for subwords)
    # - Code/punctuation: ~1 token per structural character
    # - Base character count for remaining text
    remaining_chars = len(text) - len(" ".join(words)) - code_chars

    estimated_tokens = int(
        word_count * 0.75  # Word tokens
        + code_chars * 1.0  # Code structure tokens
        + remaining_chars * 0.3  # Other characters (spaces, etc.)
    )

    return estimated_tokens


def get_model_context_window(model_id):
    """Get the actual context window size for a given model."""
    model_context_limits = {
        "claude-sonnet-4": 200000,
        "claude-3-5-sonnet-20241022": 200000,
        "claude-3-5-sonnet-20240620": 200000,
        "claude-3-5-sonnet": 200000,
        "claude-3-opus-20240229": 200000,
        "claude-3-opus": 200000,
        "claude-3-haiku-20240307": 200000,
        "claude-3-haiku": 200000,
        "claude-3-5-haiku-20241022": 200000,
        "claude-3-5-haiku": 200000,
        # Future model patterns
        "claude-4": 200000,
        "claude-3": 200000,
    }

    # Find matching model context limit (check longer patterns first)
    sorted_models = sorted(model_context_limits.items(), key=lambda x: len(x[0]), reverse=True)

    for model_key, context_limit in sorted_models:
        if model_key in model_id.lower():
            debug_print(f"Matched model {model_key} with context window {context_limit}")
            return context_limit

    # Default fallback for unknown models
    debug_print(f"Unknown model context window for: {model_id}, using 200k default")
    return 200000


def find_last_clear_index(messages):
    """Find the index of the most recent /clear command in messages."""
    last_clear_index = -1

    for i, msg in enumerate(messages):
        # Handle different message formats for finding /clear commands
        content = ""
        msg_type = msg.get("type", "")

        # Only check user messages for /clear commands
        if msg_type != "user":
            continue

        # Extract content from the new format: message.content[].text
        if "message" in msg and isinstance(msg["message"], dict):
            message_obj = msg["message"]
            if "content" in message_obj:
                msg_content = message_obj["content"]
                if isinstance(msg_content, str):
                    content = msg_content
                elif isinstance(msg_content, list):
                    # Handle structured content like [{"type": "text", "text": "..."}]
                    for item in msg_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            content += item.get("text", "")
        elif "content" in msg:
            # Old format: content at top level
            content = str(msg["content"])

        # Check for /clear command (could be at start of message or standalone)
        if content.strip() == "/clear" or content.startswith("/clear ") or "/clear" in content:
            last_clear_index = i
            debug_print(f"Found /clear command at message index {i}: '{content[:50]}...'")

    return last_clear_index


def get_context_usage_from_transcript(transcript_path, model_id):
    """Get authoritative context usage from Claude Code transcript usage data."""
    try:
        if not os.path.exists(transcript_path):
            debug_print(f"Transcript file not found: {transcript_path}")
            return None, None

        # Get model's actual context window
        total_context = get_model_context_window(model_id)

        # Parse transcript to get messages with usage data
        messages = []
        with open(transcript_path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        messages.append(entry)
                    except json.JSONDecodeError as e:
                        debug_print(f"JSON decode error in transcript: {e}")
                        continue

        if not messages:
            debug_print("No parseable messages found in transcript")
            return total_context // 2, total_context

        debug_print(f"Parsed {len(messages)} messages from transcript")

        # Find the most recent /clear command
        last_clear_index = find_last_clear_index(messages)

        # Only count tokens from messages after the most recent /clear
        if last_clear_index >= 0:
            active_messages = messages[last_clear_index + 1 :]
            debug_print(
                f"Found /clear at index {last_clear_index}, using {len(active_messages)} messages after clear"
            )
        else:
            active_messages = messages
            debug_print(f"No /clear found, using all {len(active_messages)} messages")

        # Find the most recent message with usage data to get current context state
        latest_usage = None
        messages_with_usage = 0

        for i in reversed(range(len(active_messages))):
            msg = active_messages[i]
            # Handle multiple formats for usage data
            usage = None
            msg_type = msg.get("type", "")

            # Skip non-message entries (like summaries)
            if msg_type not in ["user", "assistant"]:
                debug_print(f"Message {i}: Skipping type '{msg_type}'")
                continue

            # Try different usage data locations
            if "usage" in msg:
                # Old format: usage at top level
                usage = msg["usage"]
                debug_print(f"Message {i}: Found usage at top level")
            elif "message" in msg and isinstance(msg["message"], dict):
                # New format: check under message
                message_obj = msg["message"]
                if "usage" in message_obj:
                    usage = message_obj["usage"]
                    debug_print(f"Message {i}: Found usage under message")
                else:
                    debug_print(f"Message {i}: message object keys: {list(message_obj.keys())}")
            else:
                debug_print(f"Message {i}: Top-level keys: {list(msg.keys())}")

            if usage:
                messages_with_usage += 1
                # Use the most recent usage data as it reflects current context state
                if latest_usage is None:
                    latest_usage = usage
                    debug_print(
                        f"Message {i} tokens - input: {usage.get('input_tokens', 0)}, "
                        f"cache_read: {usage.get('cache_read_input_tokens', 0)}, "
                        f"cache_creation: {usage.get('cache_creation_input_tokens', 0)}, "
                        f"output: {usage.get('output_tokens', 0)}"
                    )
                    break
            else:
                debug_print(f"Message {i}: No usage data found")

        debug_print(
            f"Found {messages_with_usage} messages with usage data out of {len(active_messages)} total"
        )

        # If we have recent usage data, estimate remaining context
        if latest_usage:
            # Use the most recent total token count as current context usage
            current_tokens_used = 0
            current_tokens_used += latest_usage.get("input_tokens", 0)
            current_tokens_used += latest_usage.get("cache_read_input_tokens", 0)
            current_tokens_used += latest_usage.get("cache_creation_input_tokens", 0)
            current_tokens_used += latest_usage.get("output_tokens", 0)

            estimated_remaining = total_context - current_tokens_used
            # Ensure remaining doesn't go negative
            estimated_remaining = max(0, estimated_remaining)
            debug_print(
                f"Using latest usage data: {current_tokens_used} used, {estimated_remaining} remaining of {total_context}"
            )
            return estimated_remaining, total_context

        # Fallback to estimation if no usage data is available
        debug_print("No usage data found, falling back to estimation")
        return estimate_context_usage_fallback(active_messages, total_context)

    except Exception as e:
        debug_print(f"Error reading authoritative context usage: {e}")
        debug_print(f"Traceback: {traceback.format_exc()}")
        # Fallback to conservative estimate
        total_context = get_model_context_window(model_id)
        return int(total_context * 0.6), total_context


def estimate_context_usage_fallback(messages, total_context):
    """Fallback estimation when no usage data is available."""
    try:
        if not messages:
            return total_context // 2, total_context

        # Use existing precise token counting for fallback
        total_tokens_used = 0
        for msg in messages:
            content = str(msg.get("content", ""))
            msg_tokens = count_tokens_precisely(content)
            total_tokens_used += msg_tokens
            # Add overhead for message structure
            total_tokens_used += 10

        # Add system prompt overhead
        system_overhead = 1000
        total_tokens_used += system_overhead

        # Ensure reasonable bounds
        total_tokens_used = min(total_tokens_used, int(total_context * 0.8))
        estimated_remaining = total_context - total_tokens_used

        debug_print(
            f"Fallback estimation: {len(messages)} messages, {total_tokens_used} tokens used, {estimated_remaining} remaining"
        )
        return estimated_remaining, total_context

    except Exception as e:
        debug_print(f"Error in fallback estimation: {e}")
        return int(total_context * 0.6), total_context


def estimate_session_cost(input_data):
    """Calculate session cost using authoritative token usage data from transcript."""
    try:
        model_id = input_data.get("model", {}).get("id", "")
        transcript_path = input_data.get("transcript_path", "")

        if not transcript_path or not os.path.exists(transcript_path):
            return ""

        # Pricing per 1M tokens (approximate as of 2025)
        model_pricing = {
            "claude-sonnet-4": {
                "input": 3.00,
                "output": 15.00,
                "cache_read": 0.30,
                "cache_creation": 3.75,
            },
            "claude-3-5-sonnet-20241022": {
                "input": 3.00,
                "output": 15.00,
                "cache_read": 0.30,
                "cache_creation": 3.75,
            },
            "claude-3-5-sonnet-20240620": {
                "input": 3.00,
                "output": 15.00,
                "cache_read": 0.30,
                "cache_creation": 3.75,
            },
            "claude-3-5-sonnet": {
                "input": 3.00,
                "output": 15.00,
                "cache_read": 0.30,
                "cache_creation": 3.75,
            },
            "claude-3-opus-20240229": {
                "input": 15.00,
                "output": 75.00,
                "cache_read": 1.50,
                "cache_creation": 18.75,
            },
            "claude-3-opus": {
                "input": 15.00,
                "output": 75.00,
                "cache_read": 1.50,
                "cache_creation": 18.75,
            },
            "claude-3-haiku-20240307": {
                "input": 0.25,
                "output": 1.25,
                "cache_read": 0.03,
                "cache_creation": 0.30,
            },
            "claude-3-haiku": {
                "input": 0.25,
                "output": 1.25,
                "cache_read": 0.03,
                "cache_creation": 0.30,
            },
            "claude-3-5-haiku-20241022": {
                "input": 1.00,
                "output": 5.00,
                "cache_read": 0.10,
                "cache_creation": 1.25,
            },
            "claude-3-5-haiku": {
                "input": 1.00,
                "output": 5.00,
                "cache_read": 0.10,
                "cache_creation": 1.25,
            },
        }

        # Determine model pricing (check longer patterns first)
        pricing = None
        sorted_pricing = sorted(model_pricing.items(), key=lambda x: len(x[0]), reverse=True)
        for model_key, model_price in sorted_pricing:
            if model_key in model_id.lower():
                pricing = model_price
                debug_print(f"Matched pricing for model {model_key}")
                break

        if not pricing:
            debug_print(f"Unknown model for pricing: {model_id}")
            return ""

        # Parse transcript to get messages with usage data
        messages = []
        with open(transcript_path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        messages.append(entry)
                    except json.JSONDecodeError:
                        continue

        if not messages:
            debug_print("No messages found for cost calculation")
            return ""

        # Find the most recent /clear command
        last_clear_index = find_last_clear_index(messages)

        # Only count tokens from messages after the most recent /clear
        if last_clear_index >= 0:
            active_messages = messages[last_clear_index + 1 :]
            debug_print(f"Cost calculation using {len(active_messages)} messages after /clear")
        else:
            active_messages = messages
            debug_print(f"Cost calculation using all {len(active_messages)} messages")

        # Sum tokens by type using authoritative data
        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_read_tokens = 0
        total_cache_creation_tokens = 0
        messages_with_usage = 0

        for i, msg in enumerate(active_messages):
            # Handle multiple formats for usage data
            usage = None
            msg_type = msg.get("type", "")

            # Skip non-message entries (like summaries)
            if msg_type not in ["user", "assistant"]:
                debug_print(f"Cost message {i}: Skipping type '{msg_type}'")
                continue

            # Try different usage data locations
            if "usage" in msg:
                # Old format: usage at top level
                usage = msg["usage"]
            elif "message" in msg and isinstance(msg["message"], dict):
                # New format: check under message
                message_obj = msg["message"]
                if "usage" in message_obj:
                    usage = message_obj["usage"]

            if usage:
                total_input_tokens += usage.get("input_tokens", 0)
                total_output_tokens += usage.get("output_tokens", 0)
                total_cache_read_tokens += usage.get("cache_read_input_tokens", 0)
                total_cache_creation_tokens += usage.get("cache_creation_input_tokens", 0)
                messages_with_usage += 1
                debug_print(f"Cost message {i}: found usage data")

        debug_print(
            f"Cost calculation tokens - input: {total_input_tokens}, output: {total_output_tokens}, "
            f"cache_read: {total_cache_read_tokens}, cache_creation: {total_cache_creation_tokens}"
        )

        # If we have authoritative usage data, calculate precise cost
        if messages_with_usage > 0:
            input_cost = (total_input_tokens / 1_000_000) * pricing["input"]
            output_cost = (total_output_tokens / 1_000_000) * pricing["output"]
            cache_read_cost = (total_cache_read_tokens / 1_000_000) * pricing.get("cache_read", 0)
            cache_creation_cost = (total_cache_creation_tokens / 1_000_000) * pricing.get(
                "cache_creation", 0
            )

            total_cost = input_cost + output_cost + cache_read_cost + cache_creation_cost
            debug_print(
                f"Precise cost calculation: ${total_cost:.4f} (input: ${input_cost:.4f}, output: ${output_cost:.4f}, cache_read: ${cache_read_cost:.4f}, cache_creation: ${cache_creation_cost:.4f})"
            )
        else:
            # Fallback to estimation if no usage data available
            debug_print("No usage data available, using estimation for cost")
            total_cost = estimate_session_cost_fallback(active_messages, pricing)

        # Format cost display (no leading space or $ for grouped format)
        if total_cost >= 1.0:
            return f"{total_cost:.2f}"
        elif total_cost >= 0.01:
            return f"{total_cost:.3f}"
        else:
            return f"{total_cost:.4f}"

    except Exception as e:
        debug_print(f"Error calculating session cost: {e}")
        return ""


def estimate_session_cost_fallback(messages, pricing):
    """Fallback cost estimation when no usage data is available."""
    try:
        total_input_chars = 0
        total_output_chars = 0

        # Estimate based on message roles
        for msg in messages:
            content = str(msg.get("content", ""))
            role = msg.get("role", "user")
            chars = len(content)

            if role == "user":
                total_input_chars += chars
            else:
                total_output_chars += chars

        # Convert to token estimates (rough: 1 token ≈ 4 characters)
        input_tokens = total_input_chars // 4
        output_tokens = total_output_chars // 4

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        debug_print(
            f"Fallback cost estimation: ${total_cost:.4f} (input tokens: {input_tokens}, output tokens: {output_tokens})"
        )
        return total_cost

    except Exception as e:
        debug_print(f"Error in fallback cost estimation: {e}")
        return 0.0


def get_model_and_cost_info(input_data):
    """Get comprehensive model, context, and cost information."""
    try:
        model_name = input_data.get("model", {}).get("display_name", "Unknown")
        model_abbrev = get_model_abbreviation(model_name)

        debug_print(f"Getting model info for: {model_name} -> {model_abbrev}")

        # Get context information
        context_info = format_context_info(input_data)
        debug_print(f"Context info result: '{context_info}'")

        # Get session cost information
        cost_info = estimate_session_cost(input_data)
        debug_print(f"Cost info result: '{cost_info}'")

        # Create grouped model info
        grouped_model_info = format_grouped_model_info(model_abbrev, context_info, cost_info)
        debug_print(f"Final grouped model info: '{grouped_model_info}'")

        return grouped_model_info

    except Exception as e:
        debug_print(f"Error in get_model_and_cost_info: {e}")
        debug_print(f"Traceback: {traceback.format_exc()}")
        return "?"


def format_grouped_model_info(model_abbrev, context_info, cost_info):
    """Format model info in grouped format: MODEL:(CONTEXT COST)."""
    try:
        # Build the grouped content
        grouped_parts = []

        debug_print(
            f"format_grouped_model_info called with: model_abbrev='{model_abbrev}', context_info='{context_info}', cost_info='{cost_info}'"
        )

        if context_info:
            grouped_parts.append(context_info)
            debug_print(f"Added context_info: '{context_info}'")

        if cost_info:
            grouped_parts.append(f"${cost_info}")
            debug_print(f"Added cost_info: '${cost_info}'")

        if grouped_parts:
            grouped_content = " ".join(grouped_parts)
            result = f"{model_abbrev}:({grouped_content})"
            debug_print(f"Grouped result: '{result}'")
            return result
        else:
            # If no context or cost info, show basic model info with placeholder
            debug_print("No context or cost info available, showing basic model info")
            # For now, show at least the model abbreviation so we know it's working
            return f"{model_abbrev}"

    except Exception as e:
        debug_print(f"Error formatting grouped model info: {e}")
        return model_abbrev


def format_context_info(input_data):
    """Format context usage information showing used/total using authoritative data."""
    try:
        # Context percentage removed - Claude Code shows it at the bottom
        return ""

    except Exception as e:
        debug_print(f"Error formatting context info: {e}")
        return ""


def process_statusline_data(input_data):
    """Process the Claude Code input data and generate status line."""
    try:
        # Always log the complete JSON to debug file for investigation
        debug_log_path = os.path.expanduser("~/.claude/statusline_debug.log")
        try:
            with open(debug_log_path, "a") as debug_file:
                debug_file.write(f"\n=== {datetime.now().isoformat()} ===\n")
                debug_file.write(f"Complete JSON input:\n{json.dumps(input_data, indent=2)}\n")
                debug_file.write(f"Available top-level keys: {list(input_data.keys())}\n")

                # Log nested structure details
                if "workspace" in input_data:
                    debug_file.write(f"Workspace keys: {list(input_data['workspace'].keys())}\n")
                if "model" in input_data:
                    debug_file.write(f"Model keys: {list(input_data['model'].keys())}\n")
                if "context" in input_data:
                    debug_file.write(f"Context keys: {list(input_data['context'].keys())}\n")
                    debug_file.write(f"Context data: {input_data['context']}\n")

                debug_file.write("=" * 50 + "\n")
        except Exception as log_error:
            debug_print(f"Failed to write debug log: {log_error}")

        # Extract values
        cwd = input_data.get("workspace", {}).get("current_dir", os.getcwd())
        model_name = input_data.get("model", {}).get("display_name", "Unknown")
        debug_print(f"CWD: {cwd}, Model: {model_name}")

        # Get directory name (basename of path)
        dir_name = os.path.basename(cwd) or "/"
        debug_print(f"Directory name: {dir_name}")

        # Get git information and Graphite PR URL
        git_info, pr_url = get_git_info(cwd)
        debug_print(f"Git info: {git_info}")
        debug_print(f"PR URL: {pr_url}")

        # Get current branch for additional features
        current_branch = ""
        try:
            branch_result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=cwd,
                check=False,
            )
            if branch_result.returncode == 0:
                current_branch = branch_result.stdout.strip()
        except Exception as e:
            debug_print(f"Failed to get current branch: {e}")

        # Get PR status emoji
        pr_status_emoji = get_pr_status_emoji(cwd, current_branch) if current_branch else ""
        debug_print(f"PR status emoji result: '{pr_status_emoji}'")

        # Get Buildkite status
        bk_status = get_buildkite_status(cwd, current_branch) if current_branch else ""
        debug_print(f"Buildkite status result: '{bk_status}' (empty={not bool(bk_status)})")

        # Additional debug info when features are not working
        if current_branch and not bk_status:
            debug_print("Buildkite status is empty - this indicates an issue with BK detection")

        # Force debug output for PR URL detection
        if not pr_url:
            debug_print("No PR URL found - attempting direct debug...")
            # Get current branch for manual debugging
            try:
                branch_result = subprocess.run(
                    ["git", "symbolic-ref", "--short", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=cwd,
                    check=False,
                )
                if branch_result.returncode == 0:
                    current_branch = branch_result.stdout.strip()
                    debug_print(f"Current branch for PR lookup: {current_branch}")

                    # Test gt info command directly
                    try:
                        gt_test = subprocess.run(
                            ["gt", "info", current_branch],
                            capture_output=True,
                            text=True,
                            timeout=5,
                            cwd=cwd,
                            check=False,
                        )
                        debug_print(f"gt info test - return code: {gt_test.returncode}")
                        debug_print(f"gt info test - stdout: {gt_test.stdout[:200]}...")
                        debug_print(f"gt info test - stderr: {gt_test.stderr[:200]}...")
                    except Exception as e:
                        debug_print(f"gt info test failed: {e}")
            except Exception as e:
                debug_print(f"Branch lookup failed: {e}")

        # Get comprehensive model info using the dedicated function
        grouped_model_info = get_model_and_cost_info(input_data)
        debug_print(f"Final grouped model info from get_model_and_cost_info: {grouped_model_info}")

        # Build components with ANSI colors
        dir_colored = f"\033[36m{dir_name}\033[0m"  # Cyan directory
        git_colored = f"\033[37m{git_info}\033[0m"  # White git info
        grouped_model_colored = (
            f"\033[38;5;208m{grouped_model_info}\033[0m"  # Orange grouped model info
        )

        # Add Graphite PR URL with status emoji if available (in purple/magenta color)
        if pr_url:
            if pr_status_emoji:
                pr_colored = f"\033[35m {pr_status_emoji} {pr_url}\033[0m"
            else:
                pr_colored = f"\033[35m {pr_url}\033[0m"
        else:
            pr_colored = ""

        # Add Buildkite status if available (in blue color, positioned after PR)
        bk_colored = f" \033[34m{bk_status}\033[0m" if bk_status else ""

        # Build left side with git info first, then model info, then PR, then Buildkite
        left_side = f"{dir_colored}{git_colored} {grouped_model_colored}{pr_colored}{bk_colored}"

        # Calculate length without ANSI codes
        left_length = strip_ansi_length(left_side)
        debug_print(f"Left length: {left_length}")

        # Print the complete status line
        output = left_side
        debug_print(f"Final output length: {strip_ansi_length(output)}")
        return output

    except Exception as e:
        debug_print(f"General error: {e}")
        return f"➜ [Error: {e}]"


@click.command(name="schrockn-claude-code-prompt")
@click.option("--debug", is_flag=True, help="Enable debug output to stderr")
def schrockn_claude_code_prompt(debug):
    """Generate Claude Code status line prompt from stdin JSON data.

    Reads JSON input from stdin containing workspace and model information,
    then outputs a formatted status line for Claude Code.

    The status line includes:
    - Current directory name (colored cyan)
    - Git branch and status
    - Model abbreviation with context/cost info (colored orange)
    - Graphite PR URL if available (colored purple)
    - Buildkite build status if available (colored blue)

    To activate this status line, add to ~/.claude/settings.json:
    {
        "statusline": {
            "command": "dagster-dev schrockn-claude-code-prompt"
        }
    }

    Example JSON input:
    {
        "model": {"display_name": "Sonnet 4", "id": "claude-sonnet-4"},
        "workspace": {"current_dir": "/path/to/project"},
        "transcript_path": "/path/to/transcript.jsonl"
    }
    """
    try:
        # Set debug mode if requested
        if debug:
            os.environ["DEBUG_STATUSLINE"] = "1"
            # Debug mode already set via environment variable

        # Read JSON input from stdin
        stdin_input = sys.stdin.read()
        debug_print(f"Received input: {stdin_input[:100]}...")
        input_data = json.loads(stdin_input)

        # Process and output the status line
        output = process_statusline_data(input_data)
        # Use sys.stdout.write to preserve ANSI colors
        sys.stdout.write(output)
        sys.stdout.flush()

    except json.JSONDecodeError as e:
        debug_print(f"JSON decode error: {e}")
        click.echo(f"➜ [JSON Error: {e}]", nl=False, err=True)
    except Exception as e:
        debug_print(f"General error: {e}")
        click.echo(f"➜ [Error: {e}]", nl=False, err=True)
