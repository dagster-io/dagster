# Scaffold Branch Subpackage Organization

**Note: This file is machine-optimized for AI/LLM consumption and analysis.**

## Module Structure

```
dagster_dg_cli/cli/scaffold/branch/
├── __init__.py          # Package marker
├── command.py          # Main CLI command implementation
├── ai.py               # AI interaction and input processing
├── git.py              # Git operations and utilities
├── models.py           # Data models and record types
└── prompts/            # AI prompt templates
    ├── branch_name.md   # Branch name generation prompt
    └── scaffolding.md   # Content scaffolding prompt
```

## Module Responsibilities

### command.py

- **Purpose**: Main CLI command entry point
- **Key Functions**: `scaffold_branch_command()`, `is_prompt_valid_git_branch_name()`
- **Dependencies**: ai.py, git.py, models.py
- **Exports**: Click command decorator

### ai.py

- **Purpose**: AI interaction, prompt handling, input type classification
- **Key Classes**: `InputType` (ABC), `TextInputType`, `GithubIssueInputType`
- **Key Functions**: `get_branch_name_and_pr_title_from_prompt()`, `scaffold_content_for_prompt()`
- **Dependencies**: claude_utils
- **Constants**: `MAX_TURNS=20`, `INPUT_TYPES` list

### git.py

- **Purpose**: Git repository operations and utilities
- **Key Functions**: `create_git_branch()`, `create_empty_commit()`, `create_branch_and_pr()`, `has_remote_origin()`
- **Dependencies**: subprocess, GitHub CLI (gh)
- **Error Handling**: Raises `click.ClickException` on failures

### models.py

- **Purpose**: Data structures and record types
- **Key Classes**: `Session` (record type for session tracking)
- **Dependencies**: dagster_shared.record
- **Usage**: Session recording for analysis

### prompts/

- **Purpose**: AI prompt templates as external files
- **branch_name.md**: Template for generating branch names and PR titles
- **scaffolding.md**: Template for content scaffolding operations

## Data Flow

1. **Input Processing**: command.py → ai.py (input type classification)
2. **AI Generation**: ai.py → prompts/ (template loading) → claude_utils
3. **Git Operations**: command.py → git.py (branch creation, commits, PR)
4. **Session Recording**: command.py → models.py (data persistence)

## Key Patterns

- **Input Types**: Extensible pattern for different user input formats (text, GitHub URLs)
- **Template System**: External markdown files for AI prompts enable easy modification
- **Error Handling**: Consistent `click.ClickException` usage across git operations
- **Modular Design**: Clear separation between CLI, AI, Git, and data concerns

## Integration Points

- **External Commands**: `gh` (GitHub CLI), `git`, `dg` commands
- **AI Service**: Claude via dagster_dg_cli.utils.claude_utils
- **UI Components**: daggy_spinner_context for progress indication
- **Configuration**: DgContext for workspace/project settings

## Package Distribution

**CRITICAL**: When adding new `.md` files to this subpackage that should NOT be included in the package distribution, you MUST update the `setup.cfg` file at `/python_modules/libraries/dagster-dg-cli/setup.cfg` to add them to the check-manifest ignore list.

**Example**: If you add `new_file.md` that should be excluded from distribution, add this line to the `[check-manifest]` ignore section in setup.cfg:

```
dagster_dg_cli/cli/scaffold/branch/new_file.md
```

**Why**: The `check-manifest` tool validates that all version-controlled files are included in the source distribution. Documentation files like CLAUDE.md are typically excluded from distribution and need to be explicitly ignored to prevent CI failures.

**Pattern**: Use the full relative path from the package root in the ignore list.
