---
description: Create an extraction plan for documentation improvements
---

# /erk:create-extraction-plan

Analyzes session context to identify documentation gaps and creates an extraction plan issue to track the improvements.

## Prerequisites

Before running this command, ensure `docs/learned/` exists and has at least one documentation file:

```bash
# Initialize docs/learned if it doesn't exist
erk docs init

# Verify it's ready
ls docs/learned/*.md
```

If `docs/learned/` is missing or empty, the command will fail with a suggestion to run `erk docs init` first.

**Note:** Running `erk init` for a new project automatically initializes `docs/learned/` with template files (glossary.md, conventions.md, guide.md).

## Usage

```bash
/erk:create-extraction-plan [context]
```

**Arguments:**

- `[context]` - Optional. Free-form text that can specify:
  - Session ID(s) to analyze (e.g., "session abc123")
  - Focus/steering for extraction (e.g., "focus on CLI patterns")
  - Or both (e.g., "sessions abc123 and def456, focus on testing")

**Examples:**

```bash
# Analyze current conversation
/erk:create-extraction-plan

# Current conversation with focus
/erk:create-extraction-plan "focus on the CLI patterns we discussed"

# Analyze specific session log
/erk:create-extraction-plan "session abc123"

# Multiple sessions with steering
/erk:create-extraction-plan "sessions abc123 and def456, focus on testing patterns"
```

## What It Does

1. Analyzes session(s) for documentation gaps
2. Identifies both learning gaps (Category A) and teaching gaps (Category B)
3. Creates a GitHub issue with `erk-plan` + `erk-extraction` labels
4. Outputs next steps for implementation

## What You'll Get

Suggestions organized by category:

**Category A (Learning Gaps):**

- Documentation that would have made the session faster
- Usually agent docs or skills for patterns/workflows

**Category B (Teaching Gaps):**

- Documentation for what was BUILT in the session
- Usually glossary entries, routing updates, reference updates

---

## Agent Instructions

You are creating an extraction plan from session analysis.

### Step 1: Determine Source and Context

Parse the context argument (if provided) for:

1. **Session IDs** - Look for patterns like "session abc123" or UUID-like strings
2. **Steering context** - Remaining text provides focus for the extraction analysis

**If no explicit session IDs provided:**

Run the session discovery helper with size filtering to exclude tiny sessions:

```bash
erk exec list-sessions --min-size 1024
```

The JSON output includes:

- `branch_context.is_on_trunk`: Whether on main/master branch
- `current_session_id`: Current session ID from SESSION_CONTEXT env
- `sessions`: List of recent sessions with metadata (only meaningful sessions >= 1KB)
- `project_dir`: Path to session logs
- `filtered_count`: Number of tiny sessions filtered out

**Behavior based on branch context:**

**If `branch_context.is_on_trunk` is true (on main/master):**

Use `current_session_id` only. Skip user prompt - analyze current conversation.

**If `branch_context.is_on_trunk` is false (feature branch):**

First, determine if the current session is "trivial" (< 1KB, typically just launching a command like this one). Check if the current session appears in the filtered results - if not, it was filtered out as tiny.

**Common pattern**: User launches a fresh session solely to run `/erk:create-extraction-plan` on substantial work from a previous session. In this case, auto-select the substantial session(s) without prompting.

**If current session is tiny AND exactly 1 substantial session exists:**

Auto-select the substantial session without prompting. Briefly inform user:

> "Auto-selected session [id] (current session is trivial, analyzing the substantial session)"

**If current session is tiny AND 2+ substantial sessions exist:**

Auto-select ALL substantial sessions without prompting. Briefly inform user:

> "Auto-selected [N] sessions (current session is trivial, analyzing all substantial sessions)"

**If current session is substantial AND exactly 1 total session (itself):**

Proceed with current session analysis. No prompt needed.

**If current session is substantial AND other substantial sessions exist:**

Present sessions to user for selection:

> "Found these sessions for this worktree:
>
> 1. [Dec 3, 11:38 AM] 4f852cdc... - how many session ids does... (current)
> 2. [Dec 3, 11:35 AM] d8f6bb38... - no rexporting due to backwards...
> 3. [Dec 3, 11:28 AM] d82e9306... - /gt:pr-submit
>
> Which sessions should I analyze? (1=current only, 2=all, or list session numbers like '1,3')"

Wait for user selection before proceeding.

**If 0 sessions remain after filtering (all tiny including current):**

Use current session only despite being tiny. Inform user:

> "No meaningful sessions found (all sessions were < 1KB). Analyzing current conversation anyway."

**If explicit session IDs found in context:**

Load and preprocess the session logs. Session logs are stored in `project_dir` as flat files:

- Main sessions: `<session-id>.jsonl`
- Agent logs: `agent-<agent-id>.jsonl`

Match session IDs against filenames (full or partial prefix match), then preprocess:

```bash
erk exec preprocess-session <project-dir>/<session-id>.jsonl --stdout
```

### Step 2: Check for Associated Plan Issue Session Content

If on a feature branch (not trunk), check if this branch has an associated plan issue:

```bash
# Check if .impl/issue.json exists
cat .impl/issue.json 2>/dev/null
```

**If issue.json exists AND has valid `issue_number`:**

1. Extract the `issue_number` from the JSON response
2. Attempt to extract session content from the plan issue:
   ```bash
   erk exec extract-session-from-issue <issue_number> --stdout
   ```
3. If session XML is returned (not an error), store it as "plan issue session content"
4. Note the session IDs from the stderr JSON output

**If issue.json doesn't exist OR extraction fails:** Continue with session log analysis only (this is normal for branches not created via `erk implement`).

### Step 3: Verify Existing Documentation

Before analyzing gaps, scan the project for existing documentation:

```bash
# Check for existing agent docs
ls -la docs/learned/ 2>/dev/null || echo "No docs/learned/ directory"

# Check for existing skills
ls -la .claude/skills/ 2>/dev/null || echo "No .claude/skills/ directory"

# Check root-level docs
ls -la *.md README* CONTRIBUTING* 2>/dev/null
```

Create a mental inventory of what's already documented. For each potential suggestion later, verify it doesn't substantially overlap with existing docs.

### Step 4: Mine Full Session Context

**CRITICAL**: Session analysis must examine the FULL conversation, not just recent messages.

**Compaction Awareness:**

Long sessions may have been "compacted" - earlier messages summarized to save context. However:

- The pre-compaction messages are still part of the SAME LOGICAL CONVERSATION
- Valuable research, discoveries, and reasoning often occurred BEFORE compaction
- Look for compaction markers and explicitly include pre-compaction content in your analysis
- Session logs (`.jsonl` files) contain the full uncompacted conversation

**Subagent Mining:**

The Task tool spawns specialized subagents (Explore, Plan, etc.) that often do the most valuable work:

1. **Identify all Task tool invocations** - Look for `<invoke name="Task">` blocks
2. **Read subagent outputs** - Each Task returns a detailed report with discoveries
3. **Mine Explore agents** - These do codebase exploration and document what they found
4. **Mine Plan agents** - These reason through approaches and capture design decisions
5. **Don't just summarize** - Extract the specific insights, patterns, and learnings discovered

**What to look for in subagent outputs:**

- Files they read and what they learned from them
- Patterns they discovered in the codebase
- Design decisions they reasoned through
- External documentation they fetched (WebFetch, WebSearch)
- Comparisons between different approaches

**Example mining:**

If a Plan agent's output contains:

> "The existing provider pattern in data/provider.py uses ABC with abstract methods.
> This follows erk's fake-driven testing pattern where FakeProvider implements the same interface."

This indicates:

- ABC pattern documentation might need updating
- The fake-driven-testing skill connection was discovered
- This is Category A (learning) if not documented, or confirms existing docs if it is

### Steps 5-8: Analyze Session

@../../../.erk/docs/kits/erk/includes/extract-docs-analysis-shared.md

### Step 9: Combine Session Sources

When both **plan issue session content** (from Step 2) AND **session logs** (from Step 1) are available, analyze them together:

**Plan Issue Session Content** (from Step 2):

- Contains the PLANNING session - research, exploration, design decisions
- Look for: external docs consulted, codebase patterns discovered, trade-offs considered
- Particularly valuable for **Category A (Learning Gaps)** - what would have made planning faster

**Session Logs** (from Step 1):

- Contains the IMPLEMENTATION session(s) - actual work done
- Look for: features built, patterns implemented, problems solved
- Particularly valuable for **Category B (Teaching Gaps)** - documentation for what was built

When presenting analysis, clearly label which source revealed each insight:

- "[Plan session]" for insights from the plan issue
- "[Impl session]" for insights from session logs

### Step 10: Confirm with User

**If analyzing current conversation (no session IDs in context):**

Present findings neutrally and let the user decide value:

> "Based on this session, I identified these potential documentation gaps:
>
> 1. [Brief title] - [One sentence why]
> 2. [Brief title] - [One sentence why]
> 3. ...
>
> Which of these would be valuable for future sessions? I'll generate detailed suggestions and draft content for the ones you select."

**IMPORTANT: Do NOT editorialize about whether gaps are "worth" documenting, "minor", "not broadly applicable", etc. Present findings neutrally and let the user decide. Your job is to surface potential gaps, not gatekeep what's valuable.**

Wait for user response before generating full output.

**If analyzing session logs (session IDs were specified):**

Skip confirmation and output all suggestions immediately since the user explicitly chose to analyze specific session(s).

### Step 11: Format Plan Content

Format the selected suggestions as an implementation plan with this structure:

- **Objective**: Brief statement of what documentation will be added/improved
- **Source Information**: Session ID(s) that were analyzed
- **Documentation Items**: Each suggestion should include:
  - Type (Category A or B)
  - Location (where in the docs structure)
  - Action (add, update, create)
  - Priority (based on effort and impact)
  - Content (the actual draft content)

### Step 12: Create Extraction Plan Issue

**CRITICAL: Use this exact CLI command. Do NOT use `gh issue create` directly.**

Get the session ID from the `SESSION_CONTEXT` reminder in your conversation context.

```bash
erk exec create-extraction-plan \
    --plan-content="<the formatted plan content>" \
    --session-id="<session-id-from-SESSION_CONTEXT>" \
    --extraction-session-ids="<comma-separated-session-ids-that-were-analyzed>"
```

This command automatically:

1. Writes plan to `.erk/scratch/<session-id>/extraction-plan.md`
2. Creates GitHub issue with `erk-plan` + `erk-extraction` labels
3. Sets `plan_type: extraction` in plan-header metadata

**Note:** The current session ID (from `SESSION_CONTEXT` reminder) is used as `--session-id` for scratch storage. The `--extraction-session-ids` should list all session IDs that were analyzed (may differ from current session).

### Step 13: Verify and Output

Run verification to ensure the issue was created with proper Schema v2 compliance:

```bash
erk plan check <issue_number>
```

Display next steps:

```
✅ Extraction plan saved to GitHub

**Issue:** [title from result]
           [url from result]

**Next steps:**

View the plan:
    gh issue view [issue_number] --web

Implement the plan:
    erk implement [issue_number]

Submit for remote implementation:
    erk plan submit [issue_number]
```

---

## Output

After analysis (and user confirmation if applicable), display suggestions using the output format from the analysis guide, then proceed to create the extraction plan issue.
