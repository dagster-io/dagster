# PR 1: Structured Diagnostics System Implementation Plan

## Overview

Create a comprehensive diagnostics system for `dg scaffold branch` that provides visibility into the scaffolding process for rapid debugging and quality improvement. This will be the foundation for iterating on code generation quality.

## Key Implementation Tasks

### 1. Create Diagnostics Module (`diagnostics.py`)

- **Location**: `python_modules/libraries/dagster-dg-cli/dagster_dg_cli/cli/scaffold/branch/diagnostics.py`
- **Core Components**:
  - `DiagnosticsService` class using `@record` pattern
  - JSON-structured log entries with correlation IDs
  - Privacy-safe data redaction (API keys, tokens)
  - Performance timing decorators/context managers

### 2. Define Diagnostics Data Models (`models.py` updates)

- Add new record types:
  - `DiagnosticsEntry` - Individual log entry
  - `AIInteraction` - Claude prompt/response pairs with token counts
  - `ContextGathering` - Files analyzed, patterns detected
  - `PerformanceMetrics` - Timing data for each phase

### 3. Integrate with Existing Commands

- Update `command.py`:
  - Initialize diagnostics service at command start
  - Add correlation ID generation
  - Wrap key operations with diagnostics logging
  - Add `--diagnostics-level` CLI option (no environment variable)
- Update `ai.py`:
  - Log all Claude interactions (prompts, responses, tokens)
  - Track input type detection and context gathering
  - Record scaffolding decisions

### 4. Add Diagnostics Output Management

- File rotation to prevent unbounded growth
- Configurable output directory (default: `.dg/diagnostics/`)
- Add `--diagnostics-dir` CLI option

### 5. Update Claude Utils Integration

- Enhance `claude_utils.py`:
  - Add diagnostics hooks for prompt/response logging
  - Track token usage and costs
  - Log tool usage patterns

### 6. Create Tests

- Unit tests for diagnostics service
- Integration tests verifying diagnostics output
- Privacy redaction tests

### 7. Update Documentation

- **CRITICAL**: Update `CLAUDE.md` file at `python_modules/libraries/dagster-dg-cli/dagster_dg_cli/cli/scaffold/branch/CLAUDE.md`:
  - Add `diagnostics.py` to the module structure documentation
  - Document the new diagnostics data flow
  - Update integration points section
  - Add diagnostics-related CLI options to documentation

## File Changes Summary

**New Files**:

- `diagnostics.py` - Core diagnostics service
- `test_diagnostics.py` - Unit tests

**Modified Files**:

- `models.py` - Add diagnostics data models
- `command.py` - Integrate diagnostics logging
- `ai.py` - Add AI interaction logging
- `claude_utils.py` - Hook into Claude interactions
- `CLAUDE.md` - Document new architecture and files

## Success Criteria

- All scaffolding operations produce structured JSON diagnostics
- Diagnostics capture complete AI interaction history
- Performance metrics available for each phase
- Privacy-safe (no API keys in logs)
- Minimal performance impact when diagnostics disabled
- Tests pass with `make ruff` and `make quick_pyright`
- CLAUDE.md documentation is updated with new module information

## Implementation Notes

- Use `@record` pattern for all data structures
- Follow existing logging patterns from `dev.py` where applicable
- Ensure backwards compatibility (diagnostics off by default)
- Focus on rapid iteration support over production polish
- CLI flags only, no environment variable support for diagnostics level

## Documentation Requirements for All PRs

**Every PR in this workstream must**:

- Update the `CLAUDE.md` file in the scaffold/branch directory when adding new files
- Document architectural changes and new data flows
- Keep the module structure section current
- Update integration points when adding new dependencies

## Design Decisions

- **Diagnostics Storage**: JSON files in `.dg/diagnostics/` directory for machine parseability
- **Privacy**: Redact sensitive information (API keys, tokens) before logging
- **Performance**: Use timing decorators/context managers for minimal overhead
- **Correlation**: UUID-based correlation IDs to trace requests across components
- **Rotation**: Implement log rotation to prevent unbounded disk usage
- **Configuration**: CLI flags for diagnostics level and output directory
- **Integration**: Hook into existing claude_utils.py for AI interaction logging

## Testing Strategy

- Unit tests for core diagnostics service functionality
- Integration tests for end-to-end diagnostics output
- Privacy redaction validation tests
- Performance impact measurement tests
- CLI option validation tests
