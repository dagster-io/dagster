---
description: Extract insights from plan-associated sessions
argument-hint: "[issue-number]"
---

# /erk:learn

Create a documentation plan from Claude Code sessions associated with a plan implementation. The verb "learn" means: analyze what happened, extract insights, and create an actionable plan to document those learnings.

## Usage

```
/erk:learn           # Infers issue from current branch (P{issue}-...)
/erk:learn 4655      # Explicit issue number
```

## Purpose

**Audience**: All documentation produced by this command is for AI agents, not human users.

These docs are "token caches" - preserved reasoning and research so future agents don't have to recompute it. When you research something, discover a pattern, or figure out how something works, that knowledge should be captured so the next agent doesn't burn tokens rediscovering it.

**Document reality**: Capture the world as it is, not as we wish it to be. "This is non-ideal but here's the current state" is valuable documentation. Tech debt, workarounds, quirks - document them. Future agents need to know how things actually work.

**Bias toward capturing**: When uncertain whether something is worth documenting, include it. Over-documentation is better than losing insights.

**Reject dismissiveness**: If you find yourself thinking "this doesn't need documentation," pause. That instinct is often wrong. New features, patterns, and capabilities almost always benefit from documentation, even when the code is "clear."

## Agent Instructions

### Step 1: Get Session Information

Run the exec script to get session details:

```bash
erk exec get-learn-sessions <issue-number>
```

Parse the JSON output to get:

- `session_paths`: Paths to readable session files
- `planning_session_id`: Session that created the plan
- `implementation_session_ids`: Sessions that executed the plan
- `local_session_ids`: Fallback sessions found locally

If no sessions are found, inform the user and stop.

### Step 2: Analyze Implementation

Before analyzing sessions, understand what code actually changed. A smooth implementation with no errors can still add major new capabilities that need documentation.

Get the PR information for this plan:

```bash
erk exec get-pr-for-plan <issue-number>
```

This returns JSON with PR details (`number`, `title`, `state`, `url`, `head_ref_name`, `base_ref_name`) or an error if no PR exists.

Analyze the changes:

```bash
gh pr view <pr-number> --json files,additions,deletions
gh pr diff <pr-number>
```

**Create an inventory of what was built:**

- **New files**: What files were created?
- **New functions/classes**: What new APIs were added?
- **New CLI commands**: Any new `@click.command` decorators?
- **New patterns**: Any new architectural patterns established?
- **Config changes**: New settings, capabilities, or options?
- **External integrations**: New API calls, dependencies, or tools?

**Save this inventory** - you will reference it in Step 4 to ensure everything new gets documented.

#### Fetch PR Comments

If a PR was found for this plan, fetch review comments for analysis:

```bash
# Get inline review comments (code-level feedback)
erk exec get-pr-review-comments --pr <pr-number> --include-resolved

# Get discussion comments (main PR thread)
erk exec get-pr-discussion-comments --pr <pr-number>
```

**Save these for analysis** - PR comments often reveal:

- Edge cases reviewers identified
- Clarifications about non-obvious behavior
- Alternative approaches discussed
- False positives or misunderstandings to prevent

### Step 3: Gather and Analyze Sessions

#### Check Existing Documentation

Scan for existing documentation to avoid suggesting duplicates:

```bash
ls -la docs/learned/ 2>/dev/null || echo "No docs/learned/ directory"
ls -la .claude/skills/ 2>/dev/null || echo "No .claude/skills/ directory"
```

#### Analyze Current Conversation

Before preprocessing session files, analyze the current conversation context:

**You have direct access to this session.** No preprocessing needed - examine what happened:

1. **User corrections**: Did the user correct any assumptions or approaches?
2. **External lookups**: What did you WebFetch or WebSearch? Why wasn't it already documented?
3. **Unexpected discoveries**: What surprised you during implementation?
4. **Repeated patterns**: Did you do something multiple times that could be streamlined?

**Key question**: "What would have made this session faster if I'd known it beforehand?"

These insights are often the most valuable because they represent real friction encountered during implementation.

#### Preprocess Sessions

For each session path from Step 1, preprocess to compressed XML format:

```bash
mkdir -p .erk/scratch/sessions/${CLAUDE_SESSION_ID}/learn

# For the planning session:
erk exec preprocess-session "<planning-session-path>" \
    --max-tokens 20000 \
    --output-dir .erk/scratch/sessions/${CLAUDE_SESSION_ID}/learn \
    --prefix planning

# For each implementation session:
erk exec preprocess-session "<impl-session-path>" \
    --max-tokens 20000 \
    --output-dir .erk/scratch/sessions/${CLAUDE_SESSION_ID}/learn \
    --prefix impl
```

Note: The preprocessor applies deduplication, truncation, and pruning optimizations automatically. Files are auto-chunked if they exceed the token limit (20000 tokens safely under Claude's 25000 read limit). Output files include session IDs in filenames (e.g., `planning-{session-id}.xml` or `impl-{session-id}-part{N}.xml` for chunked files).

#### Save PR Comments

If PR comments were fetched in Step 2, save them for the gist:

```bash
erk exec get-pr-review-comments --pr <pr-number> --include-resolved \
    > .erk/scratch/sessions/${CLAUDE_SESSION_ID}/learn/pr-review-comments.json

erk exec get-pr-discussion-comments --pr <pr-number> \
    > .erk/scratch/sessions/${CLAUDE_SESSION_ID}/learn/pr-discussion-comments.json
```

#### Upload to Gist

Upload preprocessed session files and PR comments to a secret gist:

```bash
gh gist create --desc "Learn materials for plan #<issue-number>" .erk/scratch/sessions/${CLAUDE_SESSION_ID}/learn/*
```

Display the gist URL to the user and save it for the plan issue.

#### Deep Analysis

Read all preprocessed session files in the learn directory:

```bash
# Use Glob to find all XML files (they include session IDs and may be chunked)
ls .erk/scratch/sessions/${CLAUDE_SESSION_ID}/learn/*.xml
```

Files are named: `{prefix}-{session_id}.xml` or `{prefix}-{session_id}-part{N}.xml` for chunked files.

Read each file and mine them thoroughly.

**Compaction Awareness:** Long sessions may have been "compacted" (earlier messages summarized), but pre-compaction content still contains valuable research.

**Subagent Mining:**

1. Identify all Task tool invocations (`<invoke name="Task">`)
2. Read subagent outputs - each returns a detailed report
3. Mine Explore agents for codebase findings
4. Mine Plan agents for design decisions
5. Extract specific insights, not just summaries

**What to capture:**

- Files read and what was learned from them
- Patterns discovered in the codebase
- Design decisions and reasoning
- External documentation fetched (WebFetch, WebSearch)
- Error messages and how they were resolved

### Step 4: Identify Documentation Gaps

Based on session analysis and your Step 2 inventory, identify documentation that would help future agents.

#### Learning Gaps

What documentation would have made the session faster?

- Information not in the code (external API quirks, non-obvious interactions)
- Patterns where the "why" isn't clear from reading code alone
- Gotchas where code works but has surprising behavior
- Cross-cutting concerns not visible from any single file

**Execution discipline filter (advisory):** Some errors are execution discipline - agent should have read code more carefully. These are LESS likely to be documentation candidates, but when uncertain, include it.

**Tripwires vs conventional docs:**

- **Tripwire**: Cross-cutting concerns that apply broadly (e.g., "before using subprocess.run anywhere")
- **Conventional doc**: Module-specific or localized patterns

#### PR Comment Analysis

If PR comments were fetched in Step 2, mine them for documentation opportunities:

**Review Comments (Inline)**

| Thread | Path | Key Insight | Documentation Opportunity |
| ------ | ---- | ----------- | ------------------------- |
| ...    | ...  | ...         | ...                       |

Look for:

- **False positives**: Reviewer misunderstood something → document to prevent future confusion
- **Clarification requests**: "Why does this..." → document the reasoning
- **Suggested alternatives**: Discussed but rejected → document the decision
- **Edge case questions**: "What happens if..." → document the behavior

**Discussion Comments (Main Thread)**

| Author | Key Point | Documentation Opportunity |
| ------ | --------- | ------------------------- |
| ...    | ...       | ...                       |

Look for:

- Design discussions that led to choices
- Trade-off conversations
- Implementation details explained in prose

#### Teaching Gaps (MANDATORY)

**If you built it, document it.** This is NOT optional.

**IMPORTANT: "Self-documenting code" is NOT a valid reason to skip documentation.** Code shows WHAT but not WHY. Future agents need:

- When to use this feature (context)
- How it fits with other features (relationships)
- Edge cases and gotchas (experience)

**Reference: Common documentation locations**

| What was built            | Documentation needed                                       |
| ------------------------- | ---------------------------------------------------------- |
| New CLI command           | Document in `docs/learned/cli/` - usage, flags, examples   |
| New gateway method        | Add tripwire about ABC implementation (5 places to update) |
| New capability            | Update capability system docs, add to glossary             |
| New config option         | Add to `docs/learned/glossary.md`                          |
| New exec script           | Document purpose, inputs, outputs                          |
| New architectural pattern | Create architecture doc or add tripwire                    |
| External API integration  | Document quirks, rate limits, auth patterns discovered     |

**MANDATORY: Create an enumerated table.** For EACH item from your Step 2 inventory, you MUST produce a row:

| Item | Type | Documentation Needed? | If Yes: Location & Content | If No: Explicit Reason |
| ---- | ---- | --------------------- | -------------------------- | ---------------------- |
| ...  | ...  | Yes/No                | ...                        | ...                    |

Valid reasons for "No":

- Already documented at [location]
- Pure refactoring with no new behavior
- Internal helper with no external usage

Invalid reasons (REJECT these):

- "Code is self-documenting"
- "Patterns are discoverable in the code"
- "Well-tested so documentation unnecessary"
- "Simple/straightforward implementation"

**⚠️ CHECKPOINT: Before proceeding to Step 5**

You MUST have:

- [ ] Created the enumerated table above with ALL inventory items
- [ ] Provided explicit reasoning for every "No documentation needed" row
- [ ] At least considered each item (empty tables = incomplete analysis)

If your Step 2 inventory had N items, your table MUST have N rows.

**If no documentation needed for ANY item:**

If your enumerated table shows NO documentation needed for ANY item:

1. Re-read your table reasoning
2. Ask yourself: "Would a future agent working on similar code benefit from this?"
3. If still no documentation needed, state: "After explicit review of N inventory items, no documentation is needed because [specific reasons for top 3 items]"

Only proceed to Step 7 (skipping Step 5-6) after this explicit justification.

#### Outdated Documentation Check (MANDATORY)

**Removals and behavior changes require doc audits.** When the PR removes features or changes behavior, existing documentation may become incorrect.

**Search for documentation that references changed features:**

```bash
# Search docs for terms related to removed/changed features
grep -r "<removed-feature>" docs/learned/ .claude/commands/ .claude/skills/
```

**Categorize findings:**

| Finding                           | File | Status        | Action Needed          |
| --------------------------------- | ---- | ------------- | ---------------------- |
| Reference to removed feature      | ...  | Outdated      | Remove/update section  |
| Describes old behavior            | ...  | Incorrect     | Update to new behavior |
| Conflicts with new implementation | ...  | Contradictory | Reconcile              |

**Common patterns to check:**

- **Removed CLI flags**: Search for `--flag-name` in docs
- **Removed files/modules**: Search for import paths, file references
- **Changed behavior**: Search for behavioral descriptions that no longer apply
- **Removed modes**: Search for "three modes", "fallback", etc.

**Include outdated doc updates in the documentation plan** alongside new documentation needs.

### Step 5: Present Findings

Present findings to the user with:

1. **Summary of insights** with source attribution:
   - **[Plan]** - From planning/research phase
   - **[Impl]** - From implementation phase

2. **Proposed documentation items** - What you plan to include in the issue

3. **Ask for validation** - Are there insights to add, remove, or refine?

If the user decides to skip (no valuable insights), proceed to Step 7.

### Step 6: Create Plan Issue

**Front-load context into the issue.** Include:

1. **Rich context section**: Key files, patterns found, relevant existing docs, external resources, code examples
2. **Raw materials link**: The gist URL from Step 3
3. **Documentation items**: Location, action (create/update), draft content, source

Write the plan content and create the issue:

```bash
cat > .erk/scratch/sessions/${CLAUDE_SESSION_ID}/learn-plan.md << 'EOF'
# Documentation Plan: <title>

## Context

<rich context section>

## Raw Materials

<gist-url>

## PR Review Insights

<If applicable, insights derived from PR #X comments>

## Documentation Items

<items with location, action, draft content, source>
EOF

erk exec plan-save-to-issue \
    --plan-type learn \
    --plan-file .erk/scratch/sessions/${CLAUDE_SESSION_ID}/learn-plan.md \
    --session-id="${CLAUDE_SESSION_ID}" \
    --format display
```

Display the result:

```
Documentation plan created: <issue-url>
Raw materials: <gist-url>
```

### Step 7: Track Evaluation

**CRITICAL: Always run this step**, regardless of whether you created a plan or skipped.

This ensures `erk land` won't warn about unlearned plans:

```bash
erk exec track-learn-evaluation <issue-number> --session-id="${CLAUDE_SESSION_ID}"
```

### Tips

- Preprocessed sessions use XML: `<user>`, `<assistant>`, `<tool_use>`, `<tool_result>`
- `<tool_result>` elements with errors often reveal the most useful insights
- The more context you include in the issue, the faster the implementing agent can work
