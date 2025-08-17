# Scaffold Branch Subpackage Organization

**Note: This file is machine-optimized for AI/LLM consumption and analysis.**

## Module Structure

```
dagster_dg_cli/cli/scaffold/branch/
├── __init__.py          # Package marker
├── command.py          # Main CLI command implementation
├── ai.py               # AI interaction and input processing
├── git.py              # Git operations and utilities
├── models.py           # Session data models and record types
├── data_models.py      # Diagnostics data models (DiagnosticsEntry, AIInteraction, etc.)
├── diagnostics.py      # Structured diagnostics and logging system
├── validation.py       # Claude SDK message validation types (SDKMessage, ClaudeResult, etc.)
├── claude/             # Claude CLI integration subsystem
│   ├── __init__.py
│   ├── client.py       # Low-level Claude CLI execution and process management
│   ├── parsing.py      # SDK message parsing and validation
│   └── rendering.py    # Output formatting and rendering
├── ui/                 # User interface components (currently empty)
└── prompts/            # AI prompt templates
    ├── branch_name.md       # Branch name generation prompt
    ├── branch_name_only.md  # Branch name only generation
    ├── pr_title_only.md     # PR title only generation
    └── scaffolding.md       # Content scaffolding prompt
```

## Module Responsibilities

### command.py

- **Purpose**: Main CLI command entry point
- **Responsibilities**: Command parsing, workflow orchestration, user interaction
- **Dependencies**: ai.py, git.py, models.py
- **Exports**: Click command decorator

### ai.py

- **Purpose**: AI interaction, prompt handling, input type classification
- **Responsibilities**: Input type detection, prompt template management, AI conversation orchestration
- **Key Patterns**: Extensible input type system, template-based prompting
- **Dependencies**: claude/ subsystem for AI interactions

### git.py

- **Purpose**: Git repository operations and utilities
- **Responsibilities**: Branch creation, commit management, PR creation via GitHub CLI
- **Dependencies**: subprocess, GitHub CLI (gh)
- **Error Handling**: Raises `click.ClickException` on failures

### models.py

- **Purpose**: Session data structures and record types
- **Responsibilities**: Session tracking and workflow state management
- **Dependencies**: dagster_shared.record
- **Usage**: Session recording for analysis and workflow tracking

### data_models.py

- **Purpose**: Diagnostics-specific data structures
- **Responsibilities**: Type-safe data models for diagnostics capture
- **Dependencies**: dagster_shared.record
- **Usage**: Structured logging and diagnostics data capture

### validation.py

- **Purpose**: REMOVED - Official Claude SDK types are used directly
- **Migration**: Replaced with official claude-code-sdk message types

### diagnostics.py

- **Purpose**: Structured diagnostics and logging system for scaffold operations
- **Responsibilities**: Performance monitoring, AI interaction logging, correlation tracking
- **Architecture**: Instance-based service (no global singletons)
- **Features**:
  - Performance timing with context managers
  - AI interaction tracking with token counts and duration
  - Hierarchical logging levels (off, error, info, debug)
  - JSON-structured output with correlation IDs
  - Automatic log rotation and file management

### claude/ (Claude Code SDK Integration Subsystem)

#### claude/sdk_client.py

- **Purpose**: Claude Code SDK integration wrapper
- **Responsibilities**: SDK orchestration, diagnostics integration, output streaming
- **Dependencies**: claude-code-sdk, diagnostics.py
- **Features**: Async streaming, official SDK types, automatic error handling, cost tracking

#### Removed Files (Migrated to SDK):
- **claude/client.py**: REMOVED - Replaced with SDK calls (~332 lines → ~200 lines)  
- **claude/parsing.py**: REMOVED - SDK handles message parsing automatically
- **claude/rendering.py**: REMOVED - SDK provides built-in message formatting

### ui/

- **Purpose**: User interface components (currently empty directory)
- **Status**: Reserved for future UI components and interactive elements

### prompts/

- **Purpose**: AI prompt templates as external files
- **branch_name.md**: Template for generating branch names and PR titles
- **branch_name_only.md**: Template for generating branch names only
- **pr_title_only.md**: Template for generating PR titles only
- **scaffolding.md**: Template for content scaffolding operations

## Data Flow

1. **Diagnostics Initialization**: command.py → diagnostics.py (instance creation with correlation ID)
2. **Input Processing**: command.py → ai.py (input type classification with diagnostics instance passed)
3. **AI Generation**: ai.py → prompts/ (template loading) → claude/ subsystem (Claude Code SDK interaction)
4. **Claude SDK Execution**: claude/sdk_client.py → claude-code-sdk (official SDK) → streaming output
5. **Git Operations**: command.py → git.py (branch creation, commits, PR with performance timing)
6. **Session Recording**: command.py → models.py (data persistence)
7. **Diagnostics Output**: command.py → diagnostics.py (flush instance to JSON files on completion)

## Diagnostics Data Flow

1. **Service Creation**: `create_claude_diagnostics_service()` creates service instance with correlation ID
2. **Event Logging**: All modules log events through passed diagnostics instance
3. **AI Interaction Capture**: claude/sdk_client.py captures all Claude SDK interactions with official message types
4. **Performance Metrics**: Context managers time operations across command execution
5. **Message Validation**: claude-code-sdk provides built-in type safety with official message types
6. **Output Generation**: JSON files written to `.dg/diagnostics/` with structured data

## Key Patterns

- **Input Types**: Extensible pattern for different user input formats (text, GitHub URLs)
- **Template System**: External markdown files for AI prompts enable easy modification
- **Error Handling**: Consistent `click.ClickException` usage across git operations
- **Modular Design**: Clear separation between CLI, AI, Git, and data concerns
- **Claude SDK Integration**: claude/ subsystem provides reliable, type-safe Claude Code SDK integration
- **Official Types**: Uses official claude-code-sdk message types for guaranteed compatibility
- **Diagnostics Pattern**: Instance-based service passed explicitly to avoid global singletons
- **Correlation Tracking**: All diagnostics events tagged with correlation ID for request tracing
- **Performance Monitoring**: Context managers and decorators for non-intrusive timing

## Integration Points

- **External Commands**: `gh` (GitHub CLI), `git`, `dg` commands
- **AI Service**: Claude Code SDK via claude/ subsystem (official SDK integration)
- **UI Components**: daggy_spinner_context for progress indication
- **Configuration**: DgContext for workspace/project settings
- **Diagnostics Storage**: `.dg/diagnostics/` directory for structured logging output
- **CLI Options**: `--diagnostics-level` (off/error/info/debug), `--diagnostics-dir`
- **SDK Compatibility**: claude-code-sdk provides official message types for guaranteed integration

## Package Distribution

**CRITICAL**: When adding new `.md` files to this subpackage that should NOT be included in the package distribution, you MUST update the `setup.cfg` file at `/python_modules/libraries/dagster-dg-cli/setup.cfg` to add them to the check-manifest ignore list.

**Example**: If you add `new_file.md` that should be excluded from distribution, add this line to the `[check-manifest]` ignore section in setup.cfg:

```
dagster_dg_cli/cli/scaffold/branch/new_file.md
```

**Why**: The `check-manifest` tool validates that all version-controlled files are included in the source distribution. Documentation files like CLAUDE.md are typically excluded from distribution and need to be explicitly ignored to prevent CI failures.

**Pattern**: Use the full relative path from the package root in the ignore list.
