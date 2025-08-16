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
├── diagnostics.py      # Structured diagnostics and logging system
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
- **Dependencies**: dagster_shared.record, diagnostics.py (imports diagnostics models)
- **Usage**: Session recording for analysis, exposes diagnostics data models

### diagnostics.py

- **Purpose**: Structured diagnostics and logging system for scaffold operations
- **Key Classes**: `ClaudeDiagnosticsService`, `DiagnosticsEntry`, `AIInteraction`, `ContextGathering`, `PerformanceMetrics`
- **Key Functions**: `create_claude_diagnostics_service()`
- **Dependencies**: dagster_shared.record, json, datetime
- **Architecture**: Instance-based service (no global singletons)
- **Features**:
  - Performance timing with context managers
  - AI interaction tracking with token counts and duration
  - Hierarchical logging levels (off, error, info, debug)
  - JSON-structured output with correlation IDs
  - Automatic log rotation and file management

### prompts/

- **Purpose**: AI prompt templates as external files
- **branch_name.md**: Template for generating branch names and PR titles
- **scaffolding.md**: Template for content scaffolding operations

## Data Flow

1. **Diagnostics Initialization**: command.py → diagnostics.py (instance creation with correlation ID)
2. **Input Processing**: command.py → ai.py (input type classification with diagnostics instance passed)
3. **AI Generation**: ai.py → prompts/ (template loading) → claude_utils (with diagnostics instance passed)
4. **Git Operations**: command.py → git.py (branch creation, commits, PR with performance timing)
5. **Session Recording**: command.py → models.py (data persistence)
6. **Diagnostics Output**: command.py → diagnostics.py (flush instance to JSON files on completion)

## Diagnostics Data Flow

1. **Service Creation**: `create_claude_diagnostics_service()` creates service instance with correlation ID
2. **Event Logging**: All modules log events through passed diagnostics instance
3. **AI Interaction Capture**: claude_utils.py hooks capture all Claude API interactions via passed instance
4. **Performance Metrics**: Context managers time operations across command execution
5. **Output Generation**: JSON files written to `.dg/diagnostics/` with structured data

## Key Patterns

- **Input Types**: Extensible pattern for different user input formats (text, GitHub URLs)
- **Template System**: External markdown files for AI prompts enable easy modification
- **Error Handling**: Consistent `click.ClickException` usage across git operations
- **Modular Design**: Clear separation between CLI, AI, Git, and data concerns
- **Diagnostics Pattern**: Instance-based service passed explicitly to avoid global singletons
- **Correlation Tracking**: All diagnostics events tagged with correlation ID for request tracing
- **Performance Monitoring**: Context managers and decorators for non-intrusive timing

## Integration Points

- **External Commands**: `gh` (GitHub CLI), `git`, `dg` commands
- **AI Service**: Claude via dagster_dg_cli.utils.claude_utils (with diagnostics hooks)
- **UI Components**: daggy_spinner_context for progress indication
- **Configuration**: DgContext for workspace/project settings
- **Diagnostics Storage**: `.dg/diagnostics/` directory for structured logging output
- **CLI Options**: `--diagnostics-level` (off/error/info/debug), `--diagnostics-dir`

## Package Distribution

**CRITICAL**: When adding new `.md` files to this subpackage that should NOT be included in the package distribution, you MUST update the `setup.cfg` file at `/python_modules/libraries/dagster-dg-cli/setup.cfg` to add them to the check-manifest ignore list.

**Example**: If you add `new_file.md` that should be excluded from distribution, add this line to the `[check-manifest]` ignore section in setup.cfg:

```
dagster_dg_cli/cli/scaffold/branch/new_file.md
```

**Why**: The `check-manifest` tool validates that all version-controlled files are included in the source distribution. Documentation files like CLAUDE.md are typically excluded from distribution and need to be explicitly ignored to prevent CI failures.

**Pattern**: Use the full relative path from the package root in the ignore list.
