# Dead Code Analysis Plan

## Objective
Find dead code within the Dagster mono repo that can be safely removed without breaking functionality or public APIs.

## Analysis Approach
Analyze sections of the codebase in chunks, examining usage patterns and determining what can be safely removed.

## What Should NOT be Removed

### 1. Public APIs and Entry Points
- **CLI Commands**: Any code referenced in setup.py entry_points (dagster, dagster-daemon, dagster-webserver, etc.)
- **Public Package APIs**: Code exported in top-level __init__.py files with __all__ declarations
- **Library Entry Points**: All console_scripts and dagster_dg_cli registry modules defined in setup.py files

### 2. Test Infrastructure
- All test directories (*_tests/) and their contents - these validate functionality
- Test utilities and fixtures that may appear unused but support the testing framework

### 3. Integration Points
- Code referenced by external integrations via entry_points in setup.py
- Plugin systems and extension points
- Schema definitions and serialization code
- Migration scripts and database schema management

### 4. Configuration and Templates
- Configuration schemas and validation code
- Template files and code generation utilities
- Example code and snippets (in examples/ and docs/)

### 5. Backwards Compatibility
- Deprecated APIs that are still publicly exposed
- Legacy import paths and module aliases
- Migration utilities for version upgrades

### 6. Infrastructure Code
- Daemon and background service code
- Monitoring, logging, and observability utilities
- Docker, Kubernetes, and deployment configurations

## Codebase Structure Analysis

### Core Packages (python_modules/)
- **dagster**: Main framework (~80+ packages)
- **dagster-webserver**: Web UI 
- **dagster-graphql**: API layer
- **dagster-pipes**: Subprocess orchestration
- **dagit**: Legacy web UI (may be candidate for removal)

### Libraries (python_modules/libraries/)
- **60+ integration libraries**: AWS, GCP, Azure, databases, ML platforms, etc.
- Each library typically has setup.py with entry points
- Test directories for each library

### Examples and Documentation
- **examples/**: 40+ example projects - used for documentation and tutorials
- **docs/**: Documentation site - not executable code but referenced content

## Initial Analysis Framework

### Dead Code Detection Strategy
1. **Static Analysis**: Find unused imports, unreferenced functions, dead branches
2. **Dynamic Analysis**: Cross-reference with test coverage and usage patterns  
3. **Dependency Analysis**: Identify internal dependencies and call graphs
4. **Public API Verification**: Ensure no public APIs are affected

### Candidate Areas for Analysis (Priority Order)
1. **Legacy/deprecated code**: Search for @deprecated decorators and TODO comments
2. **Utility modules**: Helper functions that may be unused
3. **Internal APIs**: Non-public modules with limited usage
4. **Test utilities**: Redundant test helpers and fixtures
5. **Example code**: Outdated or duplicate examples

### Tools and Methods
- `grep -r` for usage pattern analysis
- `rg` (ripgrep) for fast text searching  
- AST analysis for import/usage relationships
- Test coverage reports to identify uncovered code
- Git history analysis for recently changed vs stale code

## Analysis Results

### Phase 1: Initial Dead Code Candidates Found

#### 1. Deprecated Code (PRIME CANDIDATES FOR REMOVAL)
- **dagit CLI package** (`python_modules/dagit/`): 
  - Entire package is deprecated and will be removed in Dagster 2.0
  - Only exists as thin wrapper to dagster-webserver
  - Entry points redirect to dagster-webserver CLI
  - **REMOVAL IMPACT**: Low - users should already be using dagster-webserver
  - **ACTION**: Can be safely removed in next major version

#### 2. Unused Utility Functions
- **`check_cli_execute_file_job`** in `dagster/_utils/__init__.py`:
  - Only defined, never called anywhere in codebase
  - **ACTION**: Safe to remove immediately

#### 3. TODO-Marked Code for Cleanup
- **Component deprecation markers** in airlift and sling:
  - `dagster_airlift/core/components/airflow_instance/component.py`: TODO deprecate schrockn 2025-06-10
  - `dagster_sling/components/sling_replication_collection/component.py`: TODO deprecate schrockn 2025-06-10
  - **ACTION**: Review deprecation timeline and remove if past deadline

- **GraphQL TODO removals**:
  - Multiple `path=[]` TODO remove comments in `dagster_graphql/schema/pipelines/config.py`
  - **ACTION**: Investigate if these empty path parameters can be cleaned up

#### 4. Legacy/Experimental Code
- **`examples/experimental/`** directory contains old experimental features
  - Some may be outdated or superseded by newer implementations
  - **ACTION**: Review each experimental example for relevance

### Phase 2: Additional Analysis Needed

#### 1. Vendored Code Review
- **`dagster/_vendored/dateutil/`**: Large vendored library
  - Need to verify if still necessary vs using standard dateutil
  - May contain unused portions

#### 2. Test Code Consolidation
- Multiple test utility files with potential overlap
- Some test fixtures may be duplicated across packages

### Immediate Removal Candidates (LOW RISK)

1. **dagit package** - Deprecated, ready for removal
2. **check_cli_execute_file_job function** - Unused utility function  
3. **Experimental examples** older than 1 year with no recent commits
4. **TODO-marked cleanup items** past their deadline dates

### Validation Required

1. **aiodataloader.py** - Initially appeared unused but is actually used
2. **security.py** - Small utility but actively used throughout codebase
3. **temp_file.py** - Used primarily in tests but still necessary

## Next Steps
1. **Immediate Actions**:
   - Remove `check_cli_execute_file_job` function (safe, unused)
   - Audit dagit package removal timeline 
   - Clean up TODO-marked code past deadlines

2. **Medium-term Actions**:
   - Review experimental examples for relevance
   - Analyze vendored code necessity
   - Consolidate test utilities

3. **Validation Process**:
   - Run full test suite after each removal
   - Check for hidden/indirect references via string matching
   - Verify no external documentation references removed code
