# DG Scaffold Branch Enhancement: Rapid Iteration Plan

## Purpose & Context

The `dg scaffold branch` command is our primary tool for generating feature branches with intelligent, context-aware code. This workstream focuses on transforming it from a basic scaffolding tool into a sophisticated system that understands project patterns, generates high-quality code, and enables rapid iteration on codegen quality.

**Current Problem**: Our existing scaffolding generates generic code that doesn't match project conventions, requires manual cleanup, and lacks visibility into what went wrong when generation fails.

**Our Solution**: Build an intelligent system that learns from the codebase, generates project-aware code, and provides comprehensive visibility into the generation process.

**Critical Focus**: This workstream is sequenced specifically to **tighten our feedback loop** and enable **programmatic injection of context** into the scaffolding process. Every enhancement prioritizes faster iteration between generation attempts and quality assessment.

**Documentation-First Strategy**: All context gathering, pattern detection, and best practices discovered through this process must be documented or upstreamed to official docs immediately. Our short-term measurable deliverable is documentation quality, with code generation quality serving as our objective success metric for documentation completeness.

**Key Requirements from Development Team**:

- Fast iteration cycle: scaffold → assess quality → improve context/prompts → repeat
- Dynamic injection of docstrings and best practices into prompts
- Planning mode to understand what the system intends to generate
- Debug logging to understand failures and improve quality
- Internal-facing tool optimized for rapid iteration, not production polish

## TODO Progress Tracker

### Phase 1: Core Functionality and Dev Loop

- [x] 1. Structured Diagnostics System (debug visibility)
- [x] 2. Input Type System (robust input handling)
- [x] 3. Claude Interface Abstraction (reliable AI interactions)
- [x] 4. Dynamic Planning System (planning mode)
- [ ] 5. Basic Agent Context System (project awareness)
- [ ] 6. Prompt Template System (dynamic docstring injection)
- [ ] 7. Component Metadata Enhancement (intelligent component selection)

### Phase 2: User Experience

- [ ] 8. Claude Session Management (session continuity)
- [ ] 9. Command Orchestration (cohesive workflow)
- [ ] 10. Git Safety Validation (prevent data loss)
- [ ] 11. Git Branch Operations (smart branch creation)
- [ ] 12. Intelligent Branch Naming (meaningful names)
- [ ] 13. Terminal UI Channel System (clear output)
- [ ] 14. Package Manager Abstraction (environment compatibility)

---

## Agent Implementation Guide

_This section is optimized for AI agent consumption and provides detailed implementation context._

### Development Philosophy

This enhancement prioritizes **rapid iteration on code quality** over production polish. The system should enable quick experimentation with prompts, context gathering, and generation strategies. Focus on making the feedback loop as tight as possible between scaffold attempts and quality assessment.

### Implementation Sequence

#### 1. Structured Diagnostics System

**Purpose**: Provide comprehensive visibility into the scaffolding process for rapid debugging and quality improvement.

**Key Requirements**:

- JSON-structured diagnostics for machine parseability
- Capture all AI interactions: prompts sent, responses received, token usage
- Log context gathering: what files were analyzed, patterns detected, decisions made
- Performance metrics: timing for each phase of the process
- Privacy-safe: redact sensitive information like API keys

**Implementation Approach**:

- Create a centralized diagnostics service that all components use
- Implement log rotation to prevent unbounded growth
- Write diagnostics to files for analysis and debugging
- Include correlation IDs to trace requests across components
- Add configurable diagnostics levels via environment variables or CLI flags

#### 2. Input Type System

**Purpose**: Create strongly-typed input validation that ensures data quality before expensive operations.

**Key Requirements**:

- Define clear data structures for all input types
- Implement validation with helpful, actionable error messages
- Support partial inputs with intelligent defaults
- Type coercion where appropriate (string to boolean, etc.)
- Integration with CLI parameter validation
- **Generate schema by inspecting diagnostics logs**

**Implementation Approach**:

- Use dataclasses or Pydantic models for input validation
- Create validation rules with custom error messages
- Build type coercion utilities for common conversions
- Integrate with Click parameter types for CLI consistency
- Add input sanitization for security

#### 3. Claude Interface Abstraction

**Purpose**: Create a high-level, reliable interface for AI interactions that handles edge cases and provides consistent behavior.

**Key Requirements**:

- Abstract differences between Claude API versions
- Handle streaming and batch response modes
- Implement conversation memory for multi-turn interactions
- Smart context management: what to include/exclude from context

**Implementation Approach**:

- Build adapter pattern for different Claude API versions
- Implement conversation state management with context windows
- Create cost tracking and budget enforcement
- Add response caching for similar requests

#### 4. Dynamic Planning System

**Purpose**: Generate human-readable plans that explain what the system intends to create, enabling review before execution.

**Key Requirements**:

- Analyze task description and generate structured implementation plan
- Reference actual files and patterns from the target codebase
- Estimate complexity and suggest task decomposition for large requests
- Include risk assessment and testing recommendations
- Support plan refinement based on user feedback
- Output plans in readable markdown format

**Implementation Approach**:

- Create planning templates that adapt to different task types
- Integrate with context system to reference real project patterns
- Build plan validation to ensure generated plans are actionable
- Support iterative plan refinement through conversation
- Include confidence scoring for plan elements
- **CRITICAL**: Implement bidirectional channel with Claude to enable interactive `dg scaffold branch` command sessions

#### 5. Basic Agent Context System

**Purpose**: Efficiently gather and cache comprehensive project information for AI consumption.

**Key Requirements**:

- Lazy-load project information to avoid startup delays
- Cache expensive operations like file analysis and pattern detection
- Understand Dagster project structure and conventions
- Detect existing code patterns, import styles, and naming conventions
- Maintain context across multiple scaffolding operations
- Support both small projects and large monorepos

**Implementation Approach**:

- Build extensible context providers for different types of analysis
- Implement intelligent caching with invalidation on file changes
- Create project structure analysis that understands component relationships
- Add pattern detection for common code structures and conventions
- Support incremental updates as project evolves

#### 6. Prompt Template System

**Purpose**: Enable dynamic injection of project-specific context, docstrings, and best practices into AI prompts.

**Key Requirements**:

- Composable template system with base templates and context-specific additions
- Dynamic inclusion of relevant docstrings and examples from the codebase
- Automatic prompt sizing to stay within token limits
- Support for different prompt strategies based on task complexity

**Implementation Approach**:

- Create template hierarchy: base templates, component-specific additions, context injections
- Build docstring extraction that finds relevant examples from the codebase
- Implement dynamic prompt assembly with token counting and truncation
- Create template debugging tools to understand prompt construction

#### 7. Component Metadata Enhancement

**Purpose**: Extend the component system to expose metadata necessary for intelligent component selection and configuration.

**Key Requirements**:

- Components expose available template variables and configuration schema
- Fast component discovery without instantiating components
- Include usage examples and common configuration patterns
- Support component compatibility checking and validation
- Enable component recommendation based on task requirements

**Implementation Approach**:

- Add metadata extraction methods to component base classes
- Build component registry for fast lookups and filtering
- Create component compatibility matrix and validation rules
- Include component usage examples in metadata
- Support component discovery through multiple criteria (name, capability, type)

#### 8. Claude Session Management

**Purpose**: Implement stateful session management with enterprise-grade reliability and performance.

**Key Requirements**:

- Sessions persist across command invocations
- Exponential backoff for rate limiting and transient failures
- Token counting and budget management with cost alerts
- Session state storage in user-specific directories
- Circuit breaker pattern for API unavailability

**Implementation Approach**:

- Create session storage using SQLite or JSON files
- Implement retry logic with jittered exponential backoff
- Build token usage tracking and cost estimation
- Add session cleanup and garbage collection
- Create health checking and circuit breaker logic

#### 9. Command Orchestration

**Purpose**: Wire all components into a cohesive command that feels like a native, polished CLI tool.

**Key Requirements**:

- Clear execution flow: validate → plan → generate → review → apply
- Checkpoint/resume capability for long operations
- Dry-run mode to preview changes without applying them
- Integration with existing dg command ecosystem
- Configuration file support for team defaults

**Implementation Approach**:

- Build state machine for command execution phases
- Implement checkpoint storage for resumable operations
- Create preview mode that shows planned changes
- Add configuration file parsing and validation
- Integrate with existing dg infrastructure and conventions

#### 10-14. Supporting Infrastructure

The remaining PRs provide important but non-critical functionality:

- **Git Safety & Operations**: Prevent data loss and handle branch creation intelligently
- **Intelligent Branch Naming**: Generate meaningful names following team conventions
- **Terminal UI**: Provide clear, professional output with progress indicators
- **Package Manager Abstraction**: Work across different Python package managers

These components should follow similar patterns:

- Focus on reliability and clear error messages
- Integrate with the logging and context systems
- Support configuration and customization
- Provide graceful degradation when possible

### Implementation Guidelines

Follow the coding conventions and practices outlined in:

- `CLAUDE.md` - Project-specific development practices and requirements
- `.claude/coding_conventions.md` - Type annotations and code style conventions

---

_This document prioritizes rapid iteration and quality improvement for internal development use. Implementation details may evolve based on feedback and discoveries during development._
