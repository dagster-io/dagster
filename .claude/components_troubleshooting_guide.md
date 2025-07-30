# Dagster Components Troubleshooting Guide

## Diagnostic Approach

### 1. Identify the Layer
When encountering an issue, first determine which layer is failing:

```
YAML Files → ComponentDecl → Component Instance → Dagster Definitions
    ↓             ↓              ↓                    ↓
Discovery     Parsing      Instantiation        Execution
```

**Quick diagnosis questions:**
- Does the YAML file exist and parse correctly? → Discovery/Parsing layer
- Can the component class be imported? → Component layer  
- Do template variables resolve? → Template system
- Do the generated definitions work? → Execution layer

### 2. Use Systematic Debugging
```python
# Step-by-step diagnosis
def diagnose_component_issue(yaml_path: Path):
    print("=== YAML DISCOVERY ===")
    if not yaml_path.exists():
        print(f"❌ File not found: {yaml_path}")
        return
    print(f"✅ File exists: {yaml_path}")
    
    print("=== YAML PARSING ===")
    try:
        with open(yaml_path) as f:
            yaml_content = yaml.safe_load(f)
        print(f"✅ YAML parsed: {yaml_content}")
    except Exception as e:
        print(f"❌ YAML parsing failed: {e}")
        return
    
    print("=== FILE MODEL VALIDATION ===")
    try:
        file_model = ComponentFileModel.model_validate(yaml_content)
        print(f"✅ File model valid: {file_model}")
    except Exception as e:
        print(f"❌ File model validation failed: {e}")
        return
    
    print("=== COMPONENT TYPE RESOLUTION ===")
    try:
        component_cls = resolve_component_type(file_model.type)
        print(f"✅ Component class found: {component_cls}")
    except Exception as e:
        print(f"❌ Component resolution failed: {e}")
        return
    
    print("=== TEMPLATE VARIABLE RESOLUTION ===")
    try:
        context = create_context_for_file(yaml_path)
        context = context_with_injected_scope(context, component_cls, file_model.template_vars_module)
        print(f"✅ Template variables resolved: {list(context.rendering_scope.keys())}")
    except Exception as e:
        print(f"❌ Template variable resolution failed: {e}")
        return
    
    print("=== COMPONENT INSTANTIATION ===")
    try:
        component = component_cls.load(file_model.attributes, context)
        print(f"✅ Component instantiated: {component}")
    except Exception as e:
        print(f"❌ Component instantiation failed: {e}")
        return
    
    print("=== DEFINITION GENERATION ===")
    try:
        definitions = component.build_defs(context)
        print(f"✅ Definitions generated: {len(definitions.assets)} assets, {len(definitions.jobs)} jobs")
    except Exception as e:
        print(f"❌ Definition generation failed: {e}")
        return
```

## Common Error Categories

### YAML and Discovery Errors

#### `FileNotFoundError: No such file or directory`
**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'defs/my_component.component.yaml'
```

**Causes:**
- Incorrect file path
- File not committed to version control
- Wrong working directory

**Solutions:**
```bash
# Check file exists
ls -la defs/my_component.component.yaml

# Check current directory
pwd

# Find component files
find . -name "*.component.yaml"
```

#### `yaml.scanner.ScannerError: while parsing`
**Symptoms:**
```
yaml.scanner.ScannerError: while parsing a block mapping
  in "component.yaml", line 3, column 1
```

**Causes:**
- Invalid YAML syntax (indentation, quotes, special characters)
- Mixing tabs and spaces
- Unescaped special characters in strings

**Solutions:**
```yaml
# Wrong - inconsistent indentation
type: my_project.MyComponent
attributes:
  field1: "value1"
    field2: "value2"  # Wrong indentation

# Right - consistent indentation
type: my_project.MyComponent
attributes:
  field1: "value1"
  field2: "value2"

# Wrong - unescaped special characters
attributes:
  sql_query: SELECT * FROM table WHERE column = 'value's'

# Right - properly escaped
attributes:
  sql_query: "SELECT * FROM table WHERE column = 'value''s'"
```

### Component Type Resolution Errors

#### `ModuleNotFoundError: No module named 'my_project.components'`
**Symptoms:**
```
ModuleNotFoundError: No module named 'my_project.components'
```

**Causes:**
- Component type string incorrect in YAML
- Module not in Python path
- Component class not defined in specified module

**Debug Steps:**
```python
# Check if module can be imported
import importlib
try:
    module = importlib.import_module("my_project.components")
    print(f"Module imported: {module}")
    print(f"Module contents: {dir(module)}")
except ImportError as e:
    print(f"Import failed: {e}")

# Check component type resolution
from dagster.components.core.decl import resolve_component_type
try:
    component_cls = resolve_component_type("my_project.components.MyComponent")
    print(f"Component class: {component_cls}")
except Exception as e:
    print(f"Resolution failed: {e}")
```

**Solutions:**
```yaml
# Check component type string format
type: my_project.components.MyComponent  # module.path.ClassName
```

```python
# Ensure component is defined and exported
# In my_project/components.py
import dagster as dg

class MyComponent(dg.Component, dg.Resolvable, dg.Model):
    def build_defs(self, context): ...

# Make sure it's importable
__all__ = ["MyComponent"]
```

#### `AttributeError: module 'my_project.components' has no attribute 'MyComponent'`
**Symptoms:**
```
AttributeError: module 'my_project.components' has no attribute 'MyComponent'
```

**Causes:**
- Component class name typo in YAML
- Component class not exported from module
- Component class defined in wrong module

**Debug Steps:**
```python
# Check what's available in the module
import my_project.components
print(dir(my_project.components))

# Check if class exists with different name
for name in dir(my_project.components):
    obj = getattr(my_project.components, name)
    if isinstance(obj, type) and issubclass(obj, Component):
        print(f"Found component class: {name}")
```

### Template Variable Errors

#### `jinja2.exceptions.UndefinedError: 'template_var' is undefined`
**Symptoms:**
```
jinja2.exceptions.UndefinedError: 'template_var' is undefined
```

**Causes:**
- Template variable not defined or not decorated with `@template_var`
- Template variables module not found
- Template variable function has incorrect signature

**Debug Steps:**
```python
# Check static template variables
from dagster.components.component.template_vars import get_static_template_vars, get_context_aware_static_template_vars

component_cls = MyComponent
static_vars = get_static_template_vars(component_cls)
print(f"Static template vars (no context): {static_vars}")

context = create_test_context()
context_vars = get_context_aware_static_template_vars(component_cls, context)
print(f"Context-aware template vars: {context_vars}")

# Check additional scope
additional_scope = component_cls.get_additional_scope()
print(f"Additional scope: {additional_scope}")

# Check module-level template variables
if template_vars_module:
    module = importlib.import_module(template_vars_module)
    from dagster.components.component.template_vars import find_inline_template_vars_in_module
    module_vars = find_inline_template_vars_in_module(module)
    print(f"Module template vars: {module_vars}")
```

**Solutions:**
```python
# Ensure template variable is properly decorated
@template_var  # ✅ Correct
def my_template_var(context: ComponentLoadContext) -> str:
    return "value"

# Check parameter count (0 or 1 only)
@template_var
def no_param_var() -> str:  # ✅ OK
    return "value"

@template_var  
def context_param_var(context: ComponentLoadContext) -> str:  # ✅ OK
    return "value"

@template_var
def too_many_params(context, extra_param) -> str:  # ❌ Error
    return "value"
```

#### `ValueError: Static template var 'my_var' must have 0 or 1 parameters, got 2`
**Symptoms:**
```
ValueError: Static template var 'my_var' must have 0 or 1 parameters, got 2
```

**Causes:**
- Template variable function has incorrect number of parameters
- Function signature doesn't match expected pattern

**Solutions:**
```python
# Wrong - too many parameters
@staticmethod
@template_var
def bad_template_var(context, extra_param):
    return "value"

# Right - correct parameter patterns
@staticmethod
@template_var
def no_context_var():  # 0 parameters
    return "value"

@staticmethod
@template_var
def context_var(context: ComponentLoadContext):  # 1 parameter
    return f"value_{context.path.name}"
```

#### `ValueError: Static template var 'my_var' requires context but none was provided`
**Symptoms:**
```
ValueError: Static template var 'my_var' requires context but none was provided
```

**Causes:**
- Template variable requires context but is being called from legacy path
- Component instantiation not going through proper context resolution

**Debug Steps:**
```python
# Check how component is being loaded
# Wrong way - bypasses context resolution
component = MyComponent.load(attributes, basic_context)

# Right way - goes through full pipeline
load_context, component = load_context_and_component_for_test(
    MyComponent, attributes
)
```

### Component Instantiation Errors

#### `pydantic.ValidationError: validation error for MyComponent`
**Symptoms:**
```
pydantic.ValidationError: 1 validation error for MyComponent
field_name
  field required [type=missing, input_value={'other_field': 'value'}, input_type=dict]
```

**Causes:**
- Required field missing from YAML attributes
- Field name mismatch between YAML and Component class
- Type mismatch between YAML value and Component field type

**Debug Steps:**
```python
# Check component field definitions
import inspect
component_cls = MyComponent
signature = inspect.signature(component_cls)
print(f"Component fields: {list(signature.parameters.keys())}")

# Check what's in YAML attributes
print(f"YAML attributes: {file_model.attributes}")

# Check field types
for field_name, field_info in component_cls.model_fields.items():
    print(f"Field {field_name}: type={field_info.annotation}, required={field_info.is_required()}")
```

**Solutions:**
```yaml
# Ensure all required fields are provided
type: my_project.MyComponent
attributes:
  required_field: "value"  # Don't forget required fields
  optional_field: "value"
```

```python
# Make fields optional with defaults where appropriate
class MyComponent(Component, Resolvable, Model):
    required_field: str
    optional_field: str = "default_value"  # Provide default
    nullable_field: Optional[str] = None   # Allow None
```

### Definition Generation Errors

#### `AttributeError: 'NoneType' object has no attribute 'key'`
**Symptoms:**
```
AttributeError: 'NoneType' object has no attribute 'key'
```

**Causes:**
- `build_defs()` returning None or incomplete definitions
- Assets or jobs not properly constructed
- Missing error handling in definition generation

**Debug Steps:**
```python
def debug_build_defs(component: Component, context: ComponentLoadContext):
    try:
        definitions = component.build_defs(context)
        print(f"Definitions type: {type(definitions)}")
        print(f"Assets: {len(definitions.assets) if definitions.assets else 0}")
        print(f"Jobs: {len(definitions.jobs) if definitions.jobs else 0}")
        
        # Check individual assets
        if definitions.assets:
            for i, asset in enumerate(definitions.assets):
                if asset is None:
                    print(f"❌ Asset {i} is None")
                else:
                    print(f"✅ Asset {i}: {asset.key}")
                    
    except Exception as e:
        print(f"❌ build_defs failed: {e}")
        import traceback
        traceback.print_exc()
```

**Solutions:**
```python
class MyComponent(Component, Resolvable, Model):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        assets = []
        
        # Ensure assets are properly created
        try:
            asset = create_my_asset(self.table_name)
            if asset is not None:  # Validate asset creation
                assets.append(asset)
        except Exception as e:
            # Provide helpful error context
            raise DagsterInvalidDefinitionError(
                f"Failed to create asset for {self.table_name}: {e}"
            ) from e
        
        return Definitions(assets=assets)
```

## Performance Issues

### Slow Component Loading

#### Symptoms
- Long delays during `dagster dev` startup
- Timeouts during component discovery
- High memory usage during loading

#### Diagnosis
```python
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

# Add timing to key functions
@timing_decorator
def load_component_with_timing(decl, context):
    return load_component(decl, context)
```

#### Solutions
```python
# Use lazy loading for expensive operations
class PerformantComponent(Component):
    def __init__(self, config):
        self._config = config
        self._expensive_data = None  # Don't load immediately
    
    @property
    def expensive_data(self):
        if self._expensive_data is None:
            self._expensive_data = load_expensive_data(self._config)
        return self._expensive_data
    
    def build_defs(self, context):
        # Only load expensive data when actually needed
        if self.needs_expensive_data():
            data = self.expensive_data
        return create_definitions(data)
```

### Memory Leaks

#### Symptoms
- Memory usage grows over time
- Components not garbage collected
- Large objects retained in memory

#### Diagnosis
```python
import gc
import sys

def diagnose_memory_usage():
    # Check object counts
    print(f"Total objects: {len(gc.get_objects())}")
    
    # Check for component instances
    component_instances = [obj for obj in gc.get_objects() if isinstance(obj, Component)]
    print(f"Component instances: {len(component_instances)}")
    
    # Check reference counts
    for obj in component_instances[:5]:  # Sample first 5
        print(f"Component {obj}: {sys.getrefcount(obj)} references")
```

#### Solutions
```python
# Avoid circular references
class WellBehavedComponent(Component):
    def __init__(self, config):
        self.config = config
        # Don't store parent references that create cycles
        
    def build_defs(self, context):
        # Use weak references if needed
        import weakref
        weak_context = weakref.ref(context)
        
        # Clean up resources explicitly
        try:
            return self._build_definitions(context)
        finally:
            self._cleanup_resources()
    
    def _cleanup_resources(self):
        # Release expensive resources
        if hasattr(self, '_expensive_resource'):
            del self._expensive_resource
```

## Environment-Specific Issues

### Docker/Container Issues

#### `ImportError: No module named 'my_project'`
**In containers but works locally**

**Causes:**
- Python path differences in container
- Missing dependencies in container
- File not copied to container

**Solutions:**
```dockerfile
# Ensure Python path includes your project
ENV PYTHONPATH=/app:$PYTHONPATH

# Copy all necessary files
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -e .
```

### CI/CD Issues

#### Tests pass locally but fail in CI

**Common causes:**
- Environment variable differences
- File path differences (absolute vs relative)
- Dependency version differences
- Parallel test execution issues

**Debug approach:**
```python
# Add environment debugging to tests
def test_with_env_debug():
    import os
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"Environment: {os.environ.get('DAGSTER_ENV', 'Not set')}")
    
    # Your test code here
```

### Version Compatibility Issues

#### `AttributeError: module 'dagster' has no attribute 'template_var'`

**Causes:**
- Using newer features with older Dagster version
- Version mismatch between environments

**Solutions:**
```python
# Check Dagster version
import dagster
print(f"Dagster version: {dagster.__version__}")

# Add version compatibility checks
def get_template_var_decorator():
    if hasattr(dagster, 'template_var'):
        return dagster.template_var
    else:
        raise ImportError("template_var requires Dagster >= X.Y.Z")
```

## Recovery Strategies

### Component Won't Load - Fallback Approach
```python
def load_component_with_fallback(yaml_path: Path):
    """Try to load component with progressively simpler approaches."""
    
    # Try full loading first
    try:
        return load_component_full(yaml_path)
    except Exception as e:
        print(f"Full loading failed: {e}")
    
    # Try without template variables
    try:
        return load_component_no_templates(yaml_path)
    except Exception as e:
        print(f"Loading without templates failed: {e}")
    
    # Try with minimal configuration
    try:
        return load_component_minimal(yaml_path)
    except Exception as e:
        print(f"Minimal loading failed: {e}")
    
    # Give up gracefully
    raise DagsterInvalidDefinitionError(f"Could not load component from {yaml_path}")
```

### Gradual Migration Strategy
```python
def migrate_legacy_component(legacy_yaml_path: Path, new_yaml_path: Path):
    """Migrate from old component format to new format."""
    
    # Load legacy format
    with open(legacy_yaml_path) as f:
        legacy_config = yaml.safe_load(f)
    
    # Transform to new format
    new_config = {
        "type": transform_component_type(legacy_config["type"]),
        "attributes": transform_attributes(legacy_config["attributes"]),
    }
    
    # Add new features gradually
    if "template_vars" in legacy_config:
        new_config["template_vars_module"] = transform_template_vars(
            legacy_config["template_vars"]
        )
    
    # Write new format
    with open(new_yaml_path, 'w') as f:
        yaml.dump(new_config, f)
```

This troubleshooting guide provides systematic approaches to diagnose and resolve issues in the Dagster components system, helping developers quickly identify and fix problems at any layer of the system.