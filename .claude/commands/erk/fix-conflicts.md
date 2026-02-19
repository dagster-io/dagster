---
description: Fix all merge conflicts and continue the git rebase
---

# Fix Merge Conflicts

Fix all merge conflicts and continue the git rebase.

## Steps

1. **Check status** - Run `git status` to understand the state of the rebase and identify conflicted files

2. **For each conflicted file:**

<!-- prettier-ignore -->
@../../../.erk/docs/kits/erk/includes/conflict-resolution.md

3. **After resolving all conflicts:**
   - If project memory includes a precommit check, run it and ensure no failures
   - Stage the resolved files with `git add`
   - Continue the rebase with `git rebase --continue`

4. **Loop** - If the rebase continues with more conflicts, repeat the process

5. **Verify completion** - Check git status and recent commit history to confirm success

6. **Push changes** - After rebase, the branch will have diverged from origin. Push the rebased branch:
   - For Graphite users: `gt submit` (or `gt ss`)
   - For git-only users: `git push --force-with-lease`
