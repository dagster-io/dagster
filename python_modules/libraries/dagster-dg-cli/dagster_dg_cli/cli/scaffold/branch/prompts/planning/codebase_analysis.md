# Codebase Analysis for Planning Context

You are analyzing a Dagster codebase to understand existing patterns, conventions, and structure. This analysis will inform implementation planning for new features.

## Analysis Objectives

Examine the codebase to identify:

1. **Component Usage Patterns** - How different Dagster components are typically used
2. **File Organization** - How the project structures its code and configuration
3. **Naming Conventions** - Patterns in asset names, file names, and directory structure
4. **Configuration Patterns** - How YAML configurations are structured and organized
5. **Integration Patterns** - How external systems and libraries are integrated
6. **Testing Patterns** - How tests are organized and structured

## Specific Areas to Analyze

### Component Patterns
- Examine existing `defs.yaml` files to understand component usage
- Look for patterns in asset definitions, job configurations, and resource setup
- Identify preferred component types and configuration styles

### Code Organization
- Analyze directory structure and file naming conventions
- Look for patterns in how similar functionality is grouped
- Identify where different types of code (assets, ops, resources) are placed

### Integration Examples  
- Find examples of external system integrations
- Look for patterns in environment variable usage
- Identify common dependency management approaches

### Configuration Styles
- Examine YAML structure and organization patterns
- Look for conventions in component attribute naming
- Identify patterns in environment variable and secret management

## Response Format

Provide a structured analysis covering:

1. **Component Usage Summary** - Most commonly used component types and patterns
2. **File Organization Patterns** - How code is structured and organized
3. **Naming Conventions** - Consistent patterns in naming across the codebase
4. **Configuration Patterns** - Common approaches to YAML configuration
5. **Integration Examples** - How external systems are typically integrated
6. **Recommendations** - Suggested patterns to follow for new implementations

Focus on identifying concrete, actionable patterns that can guide new feature development while maintaining consistency with the existing codebase.