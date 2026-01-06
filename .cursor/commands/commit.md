---
description: "Review git diff and commit new/modified files with AI-generated message"
---

# Commit Changes

Review the current git diff and commit new and modified files with an AI-generated commit message.

## Instructions

When this command is invoked, perform the following steps:

1. **Get Git Status**: Use `git --no-pager status` to check for changes
2. **Review Diff**: Use `git --no-pager diff` to see unstaged changes and `git --no-pager diff --cached` for staged changes
3. **Stage Changes**: Stage all new and modified files using `git add` (do not stage deletions unless they are part of a refactoring)
4. **Analyze Changes**: Review the diff to understand:
   - What files were changed
   - What functionality was added, modified, or removed
   - The scope and impact of the changes
5. **Generate Commit Message**: Create a commit message that:
   - Has a clear, descriptive subject line (50-72 characters)
   - Includes a detailed body explaining the changes
   - Follows conventional commit message best practices
   - Accurately reflects the actual changes made
6. **Commit**: Use the heredoc format as required by project rules:
   ```bash
   git commit -F - << 'EOF'
   [generated commit message]

   Assisted-by: [AI model name] via Cursor
   EOF
   ```

## Error Handling

- If there are no changes to commit, inform the user
- If git is not initialized, report the error
- If there are merge conflicts or other git errors, handle them gracefully and report to the user

## Notes

- Always use `git --no-pager` for programmatic git operations (per project rules)
- All commits must include the "Assisted-by:" line with proper AI model attribution
- The commit message should be factual and accurately describe the changes
