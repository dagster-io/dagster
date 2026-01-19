---
name: learned-docs
description: This skill should be used when writing, modifying, or reorganizing
  documentation in docs/learned/. Use when creating new documents, updating frontmatter,
  choosing categories, creating index files, updating routing tables, or moving
  files between categories. Essential for maintaining consistent documentation structure.
---

# Learned Documentation Guide

Overview: `docs/learned/` contains agent-focused documentation with:

- YAML frontmatter for routing and discovery
- Hierarchical category organization (categories listed in index below)
- Index files for category navigation
- Routing tables in AGENTS.md

## Document Registry (Auto-Generated)

@docs/learned/index.md

## Frontmatter Requirements

Every markdown file (except index.md) MUST have:

```yaml
---
title: Document Title
read_when:
  - "first condition"
  - "second condition"
---
```

### Required Fields

| Field       | Type         | Purpose                                    |
| ----------- | ------------ | ------------------------------------------ |
| `title`     | string       | Human-readable title for index tables      |
| `read_when` | list[string] | Conditions when agent should read this doc |

### Writing Effective read_when Values

- Use gerund phrases: "creating a plan", "styling CLI output"
- Be specific: "fixing merge conflicts in tests" not "tests"
- Include 2-4 conditions covering primary use cases
- Think: "An agent should read this when they are..."

Good:

```yaml
read_when:
  - "creating or closing plans"
  - "understanding plan states"
  - "working with .impl/ folders"
```

Bad:

```yaml
read_when:
  - "plans" # Too vague
  - "the user asks" # Not descriptive
```

## Documentation Structure

**Read the master index for current categories and documents:**

`docs/learned/index.md`

The index contains:

- All category paths and descriptions
- Root-level documents
- Document listings with "Read when..." conditions

## Category Placement Guidelines

1. **Match by topic** - Does the doc clearly fit one category? (see index above for categories)
2. **Match by related docs** - Are similar docs already in a category?
3. **When unclear** - Place at root level; categorize later when patterns emerge
4. **Create new category** - When 3+ related docs exist at root level

### Distinguishing cli/ vs architecture/

This is the most common confusion:

- **cli/**: Patterns for **building CLI commands** - how users interact with the tool
  - Fast-path patterns (skipping expensive ops)
  - Output formatting and styling
  - Script mode behavior
  - Command organization

- **architecture/**: **Internal implementation patterns** - how the code works
  - Gateway ABCs and dependency injection
  - Dry-run via wrapper classes
  - Shell integration constraints
  - Protocol vs ABC decisions

## Document Structure Template

```markdown
---
title: [Clear Document Title]
read_when:
  - "[first condition]"
  - "[second condition]"
---

# [Title Matching Frontmatter]

[1-2 sentence overview]

## [Main Content Sections]

[Organized content with clear headers]

## Related Topics

- [Link to related docs](../category/doc.md) - Brief description
```

## Index File Template

Each category has an `index.md` following this pattern:

```markdown
---
title: [Category] Documentation
read_when:
  - "[when to browse this category]"
---

# [Category] Documentation

[Brief category description]

## Quick Navigation

| When you need to... | Read this        |
| ------------------- | ---------------- |
| [specific task]     | [doc.md](doc.md) |

## Documents in This Category

### [Document Title]

**File:** [doc.md](doc.md)

[1-2 sentence description]

## Related Topics

- [Other Category](../other/) - Brief relevance
```

## Code in Documentation

**Critical rule**: NEVER embed Python functions that process erk data or encode business logic.

### Why This Matters

Embedded Python code in documentation:

- Is NOT under test - it silently goes stale
- Causes bugs when agents copy outdated patterns
- Encodes business assumptions (field names, conventions) that can change
- Creates maintenance burden requiring docs-code sync

PR #2681 demonstrated this: an agent copied incorrect scratch directory paths from documentation because the docs hadn't been updated when the implementation changed.

### The "Simple Function" Trap

Even "simple" functions are dangerous. A one-liner like:

```python
# DANGEROUS - encodes `agent-` prefix convention
files = [f for f in dir.glob("*.jsonl") if not f.name.startswith("agent-")]
```

Embeds a naming convention that could change. When it does, the docs become a source of bugs.

### What to REMOVE (Aggressive Stance)

Remove ALL Python `def` functions that:

- Process session logs, JSONL, or erk data
- Encode path patterns or naming conventions
- Filter, parse, or transform erk-specific data
- Implement algorithms that exist (or could exist) in production
- Show "how to" implementation patterns for erk internals

**Even if the function doesn't exist in production today**, it could be added later, creating divergence.

### What to KEEP (Narrow Exceptions)

- **JSON/YAML format examples**: Showing data structure, not processing code
- **External library patterns**: Click commands, pytest fixtures, Rich tables (teaching third-party APIs)
- **Anti-pattern demonstrations**: Code explicitly marked "WRONG" or "DON'T DO THIS"
- **Shell/bash commands**: `ls`, `jq`, `grep` for operational tasks
- **Type definitions**: Dataclass/TypedDict showing structure (not methods)

### Decision Test

Before keeping a Python code block, ask:

1. Does it contain a `def` statement? → Probably REMOVE
2. Does it process erk-specific data? → REMOVE
3. Does it encode a convention (field name, path pattern, prefix)? → REMOVE
4. Is it teaching a third-party API (Click, pytest, Rich)? → KEEP
5. Is it showing data FORMAT (not processing)? → KEEP

### Replacement Format

When removing code, replace with:

1. **Prose description** of what the operation does
2. **Source pointer** to canonical implementation
3. **CLI command** if one exists for agents to use

**Before (BAD)**:

````markdown
```python
def find_session_logs(project_dir: Path) -> list[Path]:
    """Find all main session logs (exclude agent logs)."""
    return [
        f for f in project_dir.glob("*.jsonl")
        if f.is_file() and not f.name.startswith("agent-")
    ]
```
````

**After (GOOD)**:

```markdown
Main session logs are `.jsonl` files that don't start with `agent-`. Agent
subprocess logs use the `agent-<id>.jsonl` naming convention.

To list sessions for a project, use:
erk exec list-sessions

See `preprocess_session.py` for the canonical implementation.
```

### Source Pointer Rules

- Point to source file path: `package/module.py`
- NEVER include line numbers (they go stale)
- Use backticks for file paths
- Prefer CLI commands over source pointers when available

## Reorganizing Documentation

When moving files between categories:

### Step 1: Move Files with git mv

```bash
cd docs/learned
git mv old-location/doc.md new-category/doc.md
```

### Step 2: Update Cross-References

Find all references to moved files:

```bash
grep -r "old-filename.md" docs/learned/
```

Update relative links:

- Same category: `[doc.md](doc.md)`
- Different category: `[doc.md](../category/doc.md)`
- To category index: `[Category](../category/)`

### Step 3: Update Index Files

Update Quick Navigation tables in affected index files.

### Step 4: Update AGENTS.md

If the doc was in the routing table, update the path.

### Step 5: Validate

Run `make fast-ci` to catch broken links and formatting issues.

## Updating Routing Tables

AGENTS.md contains the Quick Routing Table for agent navigation.

### When to Add Entries

- New category additions
- High-frequency tasks
- Tasks where wrong approach is common

### Entry Format

```markdown
| [Task description] | → [Link or skill] |
```

Examples:

- `| Understand project architecture | → [Architecture](docs/learned/architecture/) |`
- `| Write Python code | → Load \`dignified-python\` skill FIRST |`

## Validation

Run before committing:

```bash
make fast-ci
```

This validates:

- YAML frontmatter syntax
- Required fields present
- Markdown formatting (prettier)

## ⚠️ Generated Files - Do Not Edit Directly

The following files are **auto-generated** from frontmatter metadata:

| File                               | Source                     |
| ---------------------------------- | -------------------------- |
| `docs/learned/index.md`            | Frontmatter from all docs  |
| `docs/learned/<category>/index.md` | Frontmatter from category  |
| `docs/learned/tripwires.md`        | `tripwires:` field in docs |

**Never edit these files directly.** Changes will be overwritten.

### Workflow for Changes

1. **Edit the source frontmatter** in the relevant documentation file(s)
2. **Run sync**: `erk docs sync`
3. **Verify changes** in the generated files
4. **Commit both** the source and generated files

### Adding a New Tripwire

To add a tripwire rule:

1. Add to the `tripwires:` field in the relevant doc's frontmatter:
   ```yaml
   tripwires:
     - action: "doing something dangerous"
       warning: "Do this instead."
   ```
2. Run `erk docs sync` to regenerate `tripwires.md`

## Quick Reference

- Full navigation: [docs/learned/guide.md](docs/learned/guide.md)
- Category index: [docs/learned/index.md](docs/learned/index.md)
- Regenerate indexes: `erk docs sync`
- Run validation: `make fast-ci`
