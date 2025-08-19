# Best Practices for Scaffolding

## Directory Structure Guidelines

- **NEVER duplicate path segments** that already exist in your current working directory
- When using `dg scaffold defs`, provide paths relative to your current directory, not absolute paths that duplicate existing structure
- When in `src/<project_name>/defs/`, scaffold to subdirectories like `<component_name>/` NOT `src/<project_name>/defs/<component_name>/`
- Always check your current directory with `pwd` before scaffolding
- The path argument to `dg scaffold defs` should be a simple relative path from where you are

### Specific Examples for Common Project Structures:

#### Example 1: test-two project structure

```
If pwd shows: /path/to/test-two/src/test_two/defs/

CORRECT: dg scaffold defs dagster_dbt.DbtProjectComponent dbt_transform
WRONG:   dg scaffold defs dagster_dbt.DbtProjectComponent src/test_two/defs/dbt_transform

Result: src/test_two/defs/dbt_transform/defs.yaml ✅
NOT:    src/test_two/defs/src/test_two/defs/dbt_transform/defs.yaml ❌
```

#### Example 2: my-project structure

```
If pwd shows: /path/to/my-project/src/my_project/defs/

CORRECT: dg scaffold defs dagster_dbt.DbtProjectComponent analytics
WRONG:   dg scaffold defs dagster_dbt.DbtProjectComponent src/my_project/defs/analytics

Result: src/my_project/defs/analytics/defs.yaml ✅
NOT:    src/my_project/defs/src/my_project/defs/analytics/defs.yaml ❌
```

### Directory Check Workflow:

1. Run `pwd` first to see current directory
2. If you're already in `.../src/<project>/defs/`, use ONLY the component name as the path
3. Navigate with `cd` if needed, but prefer scaffolding from the correct directory
4. After scaffolding, verify paths don't contain duplicate segments

### Pattern Detection Rules:

- If you see repeated path segments (e.g., `/defs/` appearing twice, or project name appearing twice), you've made a nesting error
- If the final path contains the pattern `src/<project>/defs/src/<project>/defs/`, this is WRONG
- Valid paths should follow: `src/<project>/defs/<component_name>/defs.yaml`

## Template Variables

- If you require a path to a file in a defs.yaml relative to the root of the project, use the template var `{{ project_root }}`.

## Defs.yaml Schema

- The schema for the root of the defs.yaml file (using pydantic schema) is:

```python
class DefsFile(BaseModel):
    type: str
    attributes: Optional[Mapping[str, Any]] = None
    template_vars_module: Optional[str] = None
    requirements: Optional[DefsFileRequirementsModel] = None
    post_processing: Optional[Mapping[str, Any]] = None

class DefsFileRequirementsModel(BaseModel):
    """Describes dependencies for a component to load."""

    env: Optional[list[str]] = None
```
