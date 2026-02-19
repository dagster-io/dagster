---
description: Create a structured objective through guided conversation
---

# /erk:objective-create

Create a new objective through an interactive, guided process. You describe what you want to accomplish, and Claude proposes a structured objective for your approval.

## Usage

```bash
/erk:objective-create
```

---

## Agent Instructions

### Step 1: Prompt for Description

Ask the user to describe what they want to accomplish:

```
What do you want to accomplish? Describe it however makes sense to you - goals,
constraints, design decisions you've already made, context about the codebase, etc.

I'll structure it into a formal objective for your review.
```

Wait for the user's response. They may provide:

- A brief summary
- A detailed brain dump
- Existing notes or documentation
- A combination of the above

### Step 2: Analyze and Explore

Based on the user's description:

1. **Identify key elements:**
   - What is the transformation/goal?
   - What design decisions are mentioned or implied?
   - What constraints exist?
   - What's the scope?

2. **Explore the codebase if needed:**
   - If the user references specific code, read it to understand context
   - If architecture decisions are mentioned, verify current state
   - Gather enough context to propose realistic phases

3. **Capture context for downstream implementers:**

   During objective creation, you gather valuable context that would otherwise be lost: web searches, codebase exploration, user feedback, and your reasoning. **This context belongs in the objective issue.**

   Ask yourself: "What would a future agent (or human) implementing this need to know?"

   Examples of valuable context:
   - **Inventories**: Grep results showing all instances of a pattern, categorized by type
   - **Root cause analysis**: Why the current state exists, what caused the problem
   - **Codebase findings**: Relevant files, existing patterns, architectural constraints
   - **External research**: API docs, library behavior, migration guides discovered via web search
   - **Design rationale**: Why certain approaches were chosen or rejected
   - **User preferences**: Feedback and decisions made during the conversation

   This context goes in a dedicated section after the Roadmap (see template below)

### Step 3: Ask for Structure Preference

After understanding the user's goals, present structure options using AskUserQuestion:

```
How would you like the objective structured?
```

**Options:**

1. **Steelthread (Recommended)** - Phase 1A is a minimal vertical slice proving the concept works end-to-end, followed by Phase 1B to complete the feature. Best when you can demonstrate value with a partial implementation.
2. **Linear** - Sequential phases, each building on the previous. Good when infrastructure must exist before any use case works (e.g., database schema before queries).
3. **Single** - One phase, one PR. For small, focused objectives that don't need phasing.
4. **Custom** - User describes their preferred structure

**Selection guidelines:**

- **Steelthread**: Default choice. Use when feasible - it de-risks the approach early by proving the concept works.
- **Linear**: Use when Phase 1A doesn't make sense - e.g., building a new abstraction layer that has no value until complete.
- **Single**: Use for objectives small enough to implement in one PR (typically 1-2 days of work).
- **Custom**: Use when the user has a specific structure in mind.

### Step 4: Propose Structured Objective

Write a structured objective proposal and show it to the user. Use the appropriate template based on their structure choice:

#### Steelthread Template (Recommended)

```markdown
# Objective: [Clear, Concise Title]

[1-2 sentence summary of the transformation]

## Goal

[What the end state looks like - concrete examples of the new API/behavior/architecture]

## Design Decisions

- **[Decision 1]**: [rationale]
- **[Decision 2]**: [rationale]

## Roadmap

### Phase 1A: [Name] Steelthread (1 PR)

Minimal vertical slice proving the concept works end-to-end.

| Step | Description                  | Status  | PR  |
| ---- | ---------------------------- | ------- | --- |
| 1A.1 | [Minimal infrastructure]     | pending |     |
| 1A.2 | [Wire into one command/path] | pending |     |

**Test:** [End-to-end acceptance test for steelthread]

### Phase 1B: Complete [Name] (1 PR)

Fill out remaining functionality.

| Step | Description                    | Status  | PR  |
| ---- | ------------------------------ | ------- | --- |
| 1B.1 | [Extend to remaining commands] | pending |     |
| 1B.2 | [Full test coverage]           | pending |     |

**Test:** [Full acceptance criteria]

### Phase 2: [Next Component] (1 PR)

[Description]

| Step | Description | Status  | PR  |
| ---- | ----------- | ------- | --- |
| 2.1  | ...         | pending |     |

**Test:** [Verification criteria]

## Implementation Context

[Current architecture, target architecture, patterns to follow - include if helpful]

## Exploration Notes

[Context gathered during objective creation that implementers will need]

## Related Documentation

- Skills to load: [relevant skills]
- Docs to reference: [relevant docs]
```

#### Linear Template

```markdown
# Objective: [Clear, Concise Title]

[1-2 sentence summary]

## Goal

[End state description]

## Design Decisions

- **[Decision 1]**: [rationale]

## Roadmap

### Phase 1: [Foundation] (1 PR)

[Description - this phase establishes infrastructure needed by subsequent phases]

| Step | Description | Status  | PR  |
| ---- | ----------- | ------- | --- |
| 1.1  | ...         | pending |     |

**Test:** [Verification criteria]

### Phase 2: [Build on Foundation] (1 PR)

[Description - uses Phase 1 infrastructure]

| Step | Description | Status  | PR  |
| ---- | ----------- | ------- | --- |
| 2.1  | ...         | pending |     |

**Test:** [Verification criteria]

## Implementation Context

[Context for implementers]

## Exploration Notes

[Gathered context]

## Related Documentation

- Skills to load: [relevant skills]
- Docs to reference: [relevant docs]
```

#### Single Template

```markdown
# Objective: [Clear, Concise Title]

[1-2 sentence summary]

## Goal

[End state description]

## Design Decisions

- **[Decision 1]**: [rationale]

## Implementation

| Step | Description | Status  | PR  |
| ---- | ----------- | ------- | --- |
| 1    | ...         | pending |     |
| 2    | ...         | pending |     |

**Test:** [Acceptance criteria]

## Implementation Context

[Context for implementers]

## Related Documentation

- Skills to load: [relevant skills]
- Docs to reference: [relevant docs]
```

**Key structuring principles:**

1. **One PR per phase**: Each phase should be a self-contained PR that:
   - Has a coherent, reviewable scope
   - Includes its own tests (unit + integration as appropriate)
   - Leaves the system in a working state when merged

2. **Always shippable**: After each merged PR, the system must remain functional. Never leave the codebase in a broken state between phases.

3. **Test per phase**: Every phase needs a **Test:** section describing acceptance criteria. This becomes the definition of "done" for that PR.

**Section guidelines:**

- **Goal**: Always include - this is the north star
- **Design Decisions**: Include if there are meaningful choices already made
- **Roadmap**: Include for bounded objectives - break into shippable phases (1 PR each typically)
- **Principles/Guidelines**: Include for perpetual objectives instead of a roadmap
- **Implementation Context**: Include for larger refactors where current/target state matters
- **Exploration Notes**: Include when you gathered valuable context during creation (inventories, research, reasoning). This is often the most valuable section for implementers
- **Related Documentation**: Include if specific skills or docs are relevant

**For perpetual objectives**, replace the Roadmap section with:

```markdown
## Principles

- [Guiding principle 1]
- [Guiding principle 2]

## Current Focus

[What to prioritize right now - can be updated as the objective evolves]
```

After showing the proposal, ask:

```
Does this capture what you're thinking? I can adjust any section, add more detail
to the roadmap, or restructure the phases.
```

### Step 5: Iterate Until Approved

The user may:

- **Approve as-is**: Proceed to Step 6
- **Request changes**: Make the requested adjustments and show again
- **Add information**: Incorporate new details and show again
- **Restructure**: Reorganize phases/steps based on feedback

Continue iterating until the user approves.

### Step 6: Write to Plan File and Create Issue

Once approved:

1. **Write the objective to the session's plan file:**
   - Get the plan file path from the session context
   - Write the approved objective content to that file

2. **Create the GitHub issue:**

   ```bash
   erk exec objective-save-to-issue --session-id=<session-id> --format=display
   ```

3. **Report success:**

   ```
   Objective created: #<number>
   URL: <issue-url>

   Next steps:
   - Use /erk:objective-create-plan <number> to create implementation plans for specific steps
   - Track progress by updating step status in the issue
   ```

---

## Output Format

- **Start**: Single prompt asking what they want to accomplish
- **After description**: Ask for structure preference
- **After structure choice**: Show proposed structured objective
- **Iteration**: Show updated objective after each change
- **Success**: Issue number, URL, and next steps

---

## Differences from /erk:plan-save

| Feature          | /erk:plan-save      | /erk:objective-create           |
| ---------------- | ------------------- | ------------------------------- |
| Label            | `erk-plan`          | `erk-objective` only            |
| Purpose          | Implementation plan | Roadmap or perpetual focus area |
| Title suffix     | `[erk-plan]`        | None                            |
| Metadata block   | Yes                 | No                              |
| Commands section | Yes                 | No                              |
| Body content     | Metadata only       | Objective directly              |
| Input            | Existing plan file  | Interactive creation            |

---

## Types of Objectives

**Bounded objectives** - Have a clear end state and roadmap:

- "Refactor GitHub gateway into facade pattern"
- "Add dark mode support"

**Perpetual objectives** - Ongoing areas of focus without a defined end:

- "Improve test coverage"
- "Documentation maintenance"
- "Performance optimization"

The structure adapts to the type - perpetual objectives may have principles/guidelines instead of a phased roadmap.

---

## Error Cases

| Scenario                     | Action                           |
| ---------------------------- | -------------------------------- |
| User provides no description | Re-prompt with examples          |
| Not authenticated            | Report GitHub auth error         |
| Issue creation fails         | Report API error, offer to retry |
| Plan file write fails        | Report error with path           |
