# Buildkite Architecture Guide

*Reference guide for understanding and working with Dagster's Buildkite CI/CD architecture*

## Overview

This guide documents the architecture, patterns, and conventions used in Dagster's Buildkite CI/CD pipeline. Use this as a reference when adding new steps, debugging failures, or understanding the build system.

## Architecture Overview

### Directory Structure
```
.buildkite/
├── ARCHITECTURE.md              # This guide
├── dagster-buildkite/           # Main Buildkite configuration package
│   ├── dagster_buildkite/
│   │   ├── images/
│   │   │   └── versions.py      # Docker image version management
│   │   ├── steps/               # Step definitions by category
│   │   │   ├── docs.py          # Documentation-related steps
│   │   │   ├── dagster.py       # Core Dagster test steps
│   │   │   ├── test_project.py  # Test project building
│   │   │   └── ...
│   │   └── utils.py             # Shared utilities
│   └── setup.py
└── hooks/                       # Global Buildkite hooks
    ├── pre-command
    ├── post-command
    └── pre-exit
```

### Step Generation Flow

1. **Pipeline Upload**: Buildkite runs the pipeline upload step
2. **Dynamic Generation**: `dagster-buildkite` package generates steps dynamically
3. **Step Execution**: Generated steps run with appropriate Docker images and dependencies

## Core Components

### 1. Docker Images (`images/versions.py`)

**Purpose**: Manages Docker image versions used across all steps

**Key Images**:
- `buildkite-test`: Main test execution environment
- `buildkite-build-test-project-image`: For building test projects
- `test-project-base`: Base images for test projects

**Pattern**:
```python
BUILDKITE_TEST_IMAGE_VERSION: str = get_image_version("buildkite-test")

def add_test_image(step_builder: CommandStepBuilder, ver: AvailablePythonVersion):
    return step_builder.on_python_image(
        image=f"buildkite-test:py{ver.value}-{BUILDKITE_TEST_IMAGE_VERSION}",
        env=env,
    ).with_ecr_login()
```

### 2. Step Builders

**Base Pattern**: All steps follow this structure
```python
def build_example_step() -> GroupLeafStepConfiguration:
    return (
        add_test_image(
            CommandStepBuilder("Step Name"),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "command1",
            "command2", 
            "command3",
        )
        .build()
    )
```

**Key Methods**:
- `add_test_image()`: Adds Docker environment
- `.run()`: Defines commands to execute
- `.skip_if()`: Conditional execution
- `.build()`: Finalizes step configuration

### 3. Step Categories

#### Documentation Steps (`steps/docs.py`)
- **Build docs**: Full documentation build
- **Format check**: Yarn format validation
- **Docstring validation**: Python docstring checking

#### Core Test Steps (`steps/dagster.py`)
- **Dagster core tests**: Main test suites
- **Integration tests**: Cross-component testing
- **Performance tests**: Benchmarking and perf validation

#### Test Project Steps (`steps/test_project.py`)
- **Docker image building**: Test project containers
- **Multi-version testing**: Python version matrix

## Dependency Management Patterns

### Package Installation Standards

**Current Best Practice (2025)**:
```python
.run(
    "uv pip install -e python_modules/package[extras]",
    "actual_command_here",
)
```

**Legacy Pattern (still supported)**:
```python
.run(
    "pip install -e python_modules/package[extras]",
    "actual_command_here", 
)
```

### Common Installation Patterns

#### Single Package with Extras
```python
"uv pip install -e python_modules/automation[buildkite]"
```

#### Multiple Packages
```python
"uv pip install -e 'python_modules/dagster[test]' -e 'python_modules/dagster-pipes' -e 'python_modules/libraries/dagster-shared'"
```

#### Complex Dependencies
```python
"uv pip install -e python_modules/dagster[test] -e python_modules/dagster-graphql -e python_modules/automation"
```

### Package Extras Reference

#### Automation Module
```python
# python_modules/automation/setup.py
extras_require={
    "buildkite": [
        "dagster",  # Required for automation scripts that import dagster
    ]
}
```
**When to use**: Any step running automation scripts that import dagster modules

#### Dagster Core
```python
# python_modules/dagster/setup.py  
extras_require={
    "test": [...],      # Test dependencies
    "ruff": [...],      # Linting dependencies  
    "pyright": [...],   # Type checking dependencies
}
```

## Step Development Guidelines

### 1. Adding New Steps

**Template**:
```python
def build_my_new_step() -> GroupLeafStepConfiguration:
    return (
        add_test_image(
            CommandStepBuilder(":emoji: descriptive name"),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "uv pip install -e python_modules/required_package[extras]",
            "cd target_directory",
            "python -m module.command --flags",
        )
        .build()
    )
```

**Best Practices**:
- Use descriptive emoji and name for easy identification
- Install dependencies before running commands
- Use `uv pip install` for consistency
- Include required extras based on package setup.py
- Change directory before running commands if needed

### 2. Dependency Management

**Rule**: Always install packages with required extras
```python
# ❌ Wrong - missing extras
"uv pip install -e python_modules/automation"

# ✅ Correct - includes buildkite extra for dagster dependency  
"uv pip install -e python_modules/automation[buildkite]"
```

**Common Extras Needed**:
- `automation[buildkite]` - For scripts importing dagster
- `dagster[test]` - For running tests
- `dagster[ruff]` - For linting steps
- `dagster[pyright]` - For type checking

### 3. Error Handling Patterns

**Conditional Steps**:
```python
.skip_if(skip_if_no_docs_changes())  # Skip if no relevant changes
```

**Environment Variables**:
```python
add_test_image(step_builder, python_version, env=["CUSTOM_VAR"])
```

## Common Failure Patterns & Solutions

### 1. Missing Dependencies
**Symptom**: `ModuleNotFoundError: No module named 'package'`
**Solution**: Add installation command with appropriate extras

### 2. Wrong Working Directory  
**Symptom**: `FileNotFoundError` or `No such file or directory`
**Solution**: Add `cd target_directory` before commands

### 3. Missing Extras
**Symptom**: Import errors for transitive dependencies
**Solution**: Check package setup.py and include required extras

### 4. Image Version Issues
**Symptom**: `Unable to find image` or Docker pull failures
**Solution**: Check `images/versions.py` and update image versions

## Pipeline Configuration

### Main Pipeline Definition
The main pipeline configuration uses a minimal bootstrap approach:
```yaml
steps:
  - command:
    - "git config --global --add safe.directory /workdir"
    - "python -m pip install --user -e .buildkite/dagster-buildkite"
    - "LOGLEVEL=INFO ~/.local/bin/dagster-buildkite | buildkite-agent pipeline upload"
    label: ":pipeline:"
```

This approach:
1. Installs the `dagster-buildkite` package
2. Runs it to generate the full pipeline dynamically
3. Uploads the generated pipeline to Buildkite

### Dynamic Step Generation
Steps are generated programmatically in Python, allowing for:
- **Conditional steps** based on file changes
- **Matrix builds** across Python versions
- **Complex dependencies** between steps
- **Shared configuration** and patterns

## Hooks System

### Global Hooks (`hooks/`)
- **pre-command**: Environment setup, Docker cleanup
- **post-command**: Result uploading, cleanup
- **pre-exit**: Final cleanup, network pruning

### Hook Responsibilities
- Docker container/network management
- Environment variable setup
- Secret management via S3
- Build analytics and reporting

## Development Workflow

### Local Testing
```bash
# Install the buildkite package
pip install -e .buildkite/dagster-buildkite

# Generate pipeline locally (for testing)
dagster-buildkite
```

### Adding New Step Categories
1. Create new file in `steps/` directory
2. Define step builder functions
3. Export steps in main step collection
4. Update imports in package __init__.py

### Debugging Steps
1. Check step definition in appropriate `steps/` file
2. Verify Docker image and dependencies
3. Test installation commands locally
4. Check for required extras in package setup.py

## Performance Considerations

### Build Optimization
- **Parallel execution**: Steps run in parallel when possible
- **Conditional skipping**: Skip irrelevant steps based on file changes
- **Image caching**: Docker images are cached and versioned
- **Dependency caching**: Package installations leverage Docker layer caching

### Resource Management
- **Queue management**: Different queues for different resource needs
- **Agent utilization**: Steps distributed across available agents
- **Cleanup hooks**: Automatic cleanup prevents resource leaks

---

*Architecture documented: 2025-07-31*  
*For questions or updates, contact the Dagster team*