# Scaffold Branch Subpackage Documentation

**Note: This file is machine-optimized for AI/LLM consumption and analysis during active development of dg scaffold branch (2025-08-16)**

## Architecture Overview

The `dg scaffold branch` subpackage provides AI-assisted branch scaffolding with comprehensive diagnostics. It integrates the official Claude Code SDK for reliable AI interactions and includes structured logging for performance monitoring and debugging.

## Directory Structure

```
dagster_dg_cli/cli/scaffold/branch/
├── __init__.py          # Package marker
├── command.py           # Main CLI command implementation
├── ai.py                # AI interaction and input processing
├── git.py               # Git operations and utilities
├── models.py            # All data models (session, diagnostics, and record types)
├── diagnostics.py       # Structured diagnostics and logging system
├── validation.py        # Claude SDK message validation types (SDKMessage, ClaudeResult, etc.)
├── claude/              # Claude CLI integration subsystem
│   ├── __init__.py
│   ├── client.py        # Low-level Claude CLI execution and process management
│   ├── parsing.py       # SDK message parsing and validation
│   └── rendering.py     # Output formatting and rendering
├── ui/                  # User interface components (currently empty)
└── prompts/             # AI prompt templates
    ├── branch_name.md       # Branch name generation prompt
    ├── branch_name_only.md  # Branch name only generation
    ├── pr_title_only.md     # PR title only generation
    ├── best_practices.md           # Best practices for scaffolding
    └── scaffolding_instructions.md  # Content scaffolding instructions
```

## Core Modules

### Core Command Layer

#### command.py

- **Purpose**: Main CLI command entry point and workflow orchestration
- **Responsibilities**:
  - Command parsing and argument validation
  - Workflow orchestration between AI, Git, and diagnostics
  - User interaction and progress feedback
- **Dependencies**: ai.py, git.py, models.py, diagnostics.py
- **Exports**: Click command decorator for `dg scaffold branch`

#### ai.py

- **Purpose**: AI interaction and input processing orchestration
- **Responsibilities**:
  - Input type detection and classification
  - Prompt template management and loading
  - AI conversation orchestration via Claude subsystem
- **Key Features**: Extensible input type system, template-based prompting
- **Dependencies**: claude/ subsystem, prompts/ templates

#### git.py

- **Purpose**: Git repository operations and GitHub integration
- **Responsibilities**:
  - Branch creation and management
  - Commit operations with structured messages
  - PR creation via GitHub CLI integration
- **Dependencies**: subprocess, GitHub CLI (gh)
- **Error Handling**: Consistent `click.ClickException` usage

### Data Layer

#### models.py

- **Purpose**: Unified data models for session tracking and diagnostics
- **Responsibilities**:
  - Session tracking and workflow state management
  - Diagnostics data structures (DiagnosticsEntry, AIInteraction, etc.)
  - Performance metric data models
  - Type-safe models for all data capture
- **Dependencies**: dagster_shared.record
- **Pattern**: Uses @record decorator for immutable data structures
- **Usage**: Both workflow persistence and structured logging/metrics

#### validation.py

- **Status**: DEPRECATED - Migrated to official Claude SDK types
- **Migration**: Replaced with official claude-code-sdk message types for guaranteed compatibility

### Infrastructure Layer

#### diagnostics.py

- **Purpose**: Comprehensive diagnostics and logging system
- **Architecture**: Instance-based service (no global singletons)
- **Features**:
  - Performance timing with context managers
  - AI interaction tracking with token counts and duration
  - Hierarchical logging levels (off, error, info, debug)
  - JSON-structured output with correlation IDs
  - Automatic log rotation and file management
- **Storage**: `.dg/diagnostics/` directory with structured JSON files

### Claude Integration Subsystem

#### claude/sdk_client.py

- **Purpose**: Official Claude Code SDK integration wrapper
- **Responsibilities**:
  - SDK orchestration and lifecycle management
  - Diagnostics integration for all AI interactions
  - Output streaming and real-time feedback
- **Dependencies**: claude-code-sdk, diagnostics.py
- **Features**: Async streaming, official types, error handling, cost tracking

#### Deprecated Files (Migrated to SDK):

- **claude/client.py**: REMOVED - Replaced with SDK calls (~332 lines → ~200 lines)
- **claude/parsing.py**: REMOVED - SDK handles message parsing automatically
- **claude/rendering.py**: REMOVED - SDK provides built-in message formatting

### Supporting Directories

#### ui/

- **Status**: Reserved for future development
- **Purpose**: User interface components and interactive elements
- **Current State**: Empty directory placeholder

#### prompts/

- **Purpose**: External AI prompt templates for maintainability
- **Files**:
  - `branch_name.md`: Branch name and PR title generation
  - `branch_name_only.md`: Branch name only generation
  - `pr_title_only.md`: PR title only generation
  - `best_practices.md`: Best practices and guidelines for scaffolding operations
  - `scaffolding_instructions.md`: Step-by-step content scaffolding instructions
  - `planning_prompt.md`: Interactive planning system prompts
- **Pattern**: Markdown files for easy editing and version control

## System Architecture & Data Flow

### Primary Execution Flow

```
1. Command Entry → command.py
   ├── Diagnostics initialization with correlation ID
   ├── Input processing and type classification → ai.py
   └── Workflow orchestration

2. AI Processing → ai.py
   ├── Load prompt templates from prompts/
   ├── Input type detection and classification
   └── Claude SDK interaction → claude/sdk_client.py

3. Claude SDK Execution → claude/sdk_client.py
   ├── Official claude-code-sdk integration
   ├── Streaming output with real-time feedback
   └── Diagnostics capture for all interactions

4. Git Operations → git.py
   ├── Branch creation and management
   ├── Commit operations with structured messages
   └── PR creation via GitHub CLI

5. Session Recording → models.py
   ├── Workflow state persistence
   └── Analysis data collection

6. Diagnostics Finalization → diagnostics.py
   └── JSON output to .dg/diagnostics/ directory
```

### Diagnostics Flow

```
Service Lifecycle:
├── Creation: create_claude_diagnostics_service() with correlation ID
├── Event Logging: All modules log through diagnostics instance
├── AI Interaction Capture: SDK interactions with official types
├── Performance Timing: Context managers across operations
└── Output: Structured JSON files with correlation tracking
```

## Design Principles

### Architectural Patterns

- **Layered Architecture**: Clear separation between command, data, and infrastructure layers
- **Instance-Based Services**: No global singletons, explicit dependency injection
- **Official SDK Integration**: Uses claude-code-sdk for guaranteed compatibility
- **Template-Based AI**: External markdown files for maintainable prompts
- **Type Safety**: @record decorators and official SDK types throughout

### Error Handling Strategy

- **Consistent Exceptions**: `click.ClickException` usage across git operations
- **Graceful Degradation**: Diagnostics failures don't block main workflow
- **Official SDK Reliability**: Built-in error handling from claude-code-sdk

### Performance & Monitoring

- **Non-Intrusive Timing**: Context managers for performance measurement
- **Correlation Tracking**: All events tagged with correlation ID
- **Hierarchical Logging**: Configurable levels (off/error/info/debug)
- **Automatic Management**: Log rotation and file cleanup

## External Integrations

### Required Dependencies

- **GitHub CLI (`gh`)**: PR creation, repository operations
- **Git**: Branch management, commit operations
- **Claude Code SDK**: Official AI integration
- **Dagster Utilities**: `daggy_spinner_context`, `DgContext`

### Configuration Options

- **CLI Flags**:
  - `--diagnostics-level` (off/error/info/debug)
  - `--diagnostics-dir` (custom output location)
- **Environment**: DgContext for workspace/project settings
- **Storage**: `.dg/diagnostics/` for structured logging output

## Package Distribution

**CRITICAL**: When adding new `.md` files to this subpackage that should NOT be included in the package distribution, you MUST update the `setup.cfg` file at `/python_modules/libraries/dagster-dg-cli/setup.cfg` to add them to the check-manifest ignore list.

**Example**: If you add `new_file.md` that should be excluded from distribution, add this line to the `[check-manifest]` ignore section in setup.cfg:

```
dagster_dg_cli/cli/scaffold/branch/new_file.md
```

**Why**: The `check-manifest` tool validates that all version-controlled files are included in the source distribution. Documentation files like CLAUDE.md are typically excluded from distribution and need to be explicitly ignored to prevent CI failures.

**Pattern**: Use the full relative path from the package root in the ignore list.

## @record Usage

All data models in this subpackage use the `@record` decorator from `dagster_shared.record` instead of standard `@dataclass`.

**For comprehensive guidance on `@record` usage, patterns, and best practices, see the main documentation in `/python_modules/libraries/dagster-shared/CLAUDE.md`**
