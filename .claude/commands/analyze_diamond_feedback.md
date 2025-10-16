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

⚠️ **CRITICAL**: Only GraphQL can resolve review thread conversations. Regular PR comments DO NOT resolve the Diamond feedback threads.

**Required Steps:**

1. **Get review thread IDs**: Query GraphQL to find Diamond review thread IDs
2. **Resolve conversations**: Use GraphQL `resolveReviewThread` mutation - this is the ONLY way to mark conversations as resolved (equivalent to clicking "Resolve conversation" button in GitHub UI)
3. **Optional**: Add summary comment using `gh pr comment` for documentation

**What DOESN'T work:**

- ❌ `gh pr comment` - only adds comments, doesn't resolve conversations
- ❌ `gh api repos/.../pulls/.../comments` - can't resolve review threads
- ❌ Replying to individual comments - doesn't mark conversation as resolved

**What DOES work:**

- ✅ GraphQL `resolveReviewThread` mutation - the only method that actually resolves conversations

### Step 9: Generate Final Action Plan

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
- Access to the repository being reviewed

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
(.comments[] | select(.author.login | contains("graphite-app")) | {author: .author.login, body: .body, created: .createdAt, id: .id}),
(.reviews[] | select(.author.login | contains("graphite-app")) | {author: .author.login, body: .body, created: .submittedAt, id: .id})
'

# Get Diamond review comments (inline suggestions)
gh api repos/OWNER/REPO/pulls/$PR_NUMBER/comments --jq '
.[] | select(.user.login | contains("graphite-app")) |
{author: .user.login, body: .body, path: .path, line: .line, created: .created_at}
'

# Reply to individual review comments
gh api repos/OWNER/REPO/pulls/$PR_NUMBER/comments -X POST --field body="✅ Resolved: [reason]" --field in_reply_to=$COMMENT_ID

# Step 1: Get Diamond review thread IDs for resolving conversations
# This finds all review threads and identifies which ones contain Diamond comments
gh api graphql -f query='
query($owner: String!, $name: String!, $pr: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          comments(first: 10) {
            nodes {
              id
              databaseId
              author {
                login
              }
              body
            }
          }
        }
      }
    }
  }
}' -f owner=OWNER -f name=REPO -F pr=PR_NUMBER

# Step 2: Filter for UNRESOLVED Diamond threads and extract thread IDs
# Use jq to find unresolved threads containing Diamond comments (graphite-app author)
gh api graphql -f query='...' | jq '
.data.repository.pullRequest.reviewThreads.nodes[] |
select(.isResolved == false and (.comments.nodes[] | .author.login | contains("graphite-app"))) |
{threadId: .id, isResolved: .isResolved, diamondComment: (.comments.nodes[] | select(.author.login | contains("graphite-app")) | .body)}
'

# Step 3: Resolve specific Diamond review thread conversations
# This is equivalent to clicking "Resolve conversation" button in GitHub UI
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread {
      id
      isResolved
    }
  }
}' -f threadId="THREAD_ID_FROM_STEP_2"

# Step 4: Batch resolve multiple Diamond threads
# Process multiple thread IDs at once
for thread_id in "THREAD_ID_1" "THREAD_ID_2" "THREAD_ID_3"; do
  gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread {
        id
        isResolved
      }
    }
  }' -f threadId="$thread_id"
  echo "Resolved thread: $thread_id"
done

# Mark general comments as resolved
gh pr comment $PR_NUMBER --body "✅ Resolved Diamond feedback: Issue no longer applies"
```
