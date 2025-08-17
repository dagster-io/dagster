# Analyze Diamond Feedback

## Description

Fetches all comments for the PR associated with the current branch, identifies feedback from Diamond review tool, analyzes it, and presents a plan to address the issues.

## Usage

```bash
/analyze_diamond_feedback
```

## Implementation

### Step 1: Detect Current Branch PR

- Get the current branch name using `git branch --show-current`
- Find the associated PR using `gh pr list --head <branch-name>`
- If no PR found, check all states with `--state all`
- If still no PR, inform user that no PR exists for current branch

### Step 2: Fetch All PR Comments

- Use `gh pr view <pr-number> --json comments,reviews` to get all comments and reviews
- Parse the JSON output to extract comment details
- Combine review comments and issue comments for complete coverage

### Step 3: Identify Diamond Comments

- **Diamond operates as @graphite-app[bot]** - look for this username specifically
- Filter comments where the author login is "graphite-app" or contains "graphite-app[bot]"
- Diamond provides:
  - Code review suggestions with inline comments on specific lines
  - Empty review bodies (actual feedback is in review comments)
  - Comments marked "_Spotted by Diamond_" at the end
- Extract the Diamond feedback content from review comments, not just top-level reviews

### Step 4: Analyze Diamond Feedback

Parse Diamond comments to identify:

- Code quality issues
- Security concerns
- Performance problems
- Best practice violations
- Specific file locations and line numbers mentioned
- Severity levels (if indicated)

### Step 5: Create Action Plan

Generate a structured plan with:

- Priority levels (Critical, High, Medium, Low)
- Specific files and functions to modify
- Recommended fixes for each issue
- Estimated complexity (Simple, Moderate, Complex)
- Dependencies between fixes

### Step 6: Present Comments for Review

- Display all Diamond comments found
- Show comment details (author, timestamp, content, file/line if applicable)
- Allow user to review each comment individually
- Provide options for each comment:
  - Accept: Include in action plan
  - Reject: Mark as resolved (comment no longer applies)
  - Skip: Leave unresolved but don't include in plan

### Step 7: Validate Comment Relevance

- For accepted comments, check if the issue still exists in current code
- Compare comment context with current file state
- Auto-mark as resolved if:
  - Referenced code has been removed/changed
  - Issue has already been fixed
  - File/line no longer exists

### Step 8: Mark Comments as Resolved

- Use `gh pr review <pr-number> --comment --body "✅ Resolved: [reason]"` to add resolution comments
- For review comments, reply directly to the specific comment thread
- Use `gh pr comment <pr-number> --body "✅ Resolved Diamond feedback: [summary]"` for general resolutions
- Provide feedback on which comments were marked resolved

### Step 9: Create Action Plan

- Generate plan only for remaining valid, accepted comments
- Prioritize by severity and complexity
- Group related issues by file/component

### Step 10: Present Final Plan and Confirm

- Display the filtered action plan
- Show summary of resolved comments
- Wait for user confirmation before proceeding with fixes
- Offer to implement fixes or provide detailed guidance

## Error Handling

- Handle cases where no PR exists for current branch
- Gracefully handle API rate limits
- Inform user if no Diamond comments found
- Provide fallback options for manual PR specification

## Dependencies

- `gh` CLI tool must be authenticated
- Internet connectivity for GitHub API calls
- Access to the dagster-io/dagster repository

## Implementation Details

### Using gh CLI Commands

```bash
# Get current branch and find PR
BRANCH=$(git branch --show-current)
PR_JSON=$(gh pr list --head "$BRANCH" --json number,title,url)

# Fetch all comments and reviews
gh pr view $PR_NUMBER --json comments,reviews --jq '
{
  comments: .comments[] | {
    id: .id,
    author: .author.login,
    body: .body,
    created: .createdAt,
    url: .url
  },
  reviews: .reviews[] | {
    id: .id,
    author: .author.login,
    body: .body,
    state: .state,
    created: .submittedAt
  }
}'

# Filter for Diamond comments (corrected jq syntax)
gh pr view $PR_NUMBER --json comments,reviews --jq '
(.comments + .reviews)[] |
select(.author.login | contains("graphite-app")) |
{author: .author.login, body: .body, created: (.createdAt // .submittedAt), id: .id}
'

# Get Diamond review comments (inline suggestions)
gh api repos/OWNER/REPO/pulls/$PR_NUMBER/comments --jq '
.[] | select(.user.login | contains("graphite-app")) |
{author: .user.login, body: .body, path: .path, line: .line, created: .created_at}
'

# Mark comments as resolved
gh pr comment $PR_NUMBER --body "✅ Resolved Diamond feedback: Issue no longer applies"
gh pr review $PR_NUMBER --comment --body "✅ Resolved: Code has been updated per feedback"
```
