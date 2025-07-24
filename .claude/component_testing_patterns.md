# Component Testing Patterns

This document provides comprehensive guidance for testing Dagster component **classes** (classes that extend `dagster.Component`). This guidance is for testing the behavior of new component types you are developing, not for testing specific component instances within a Dagster project. These patterns are based on analysis of existing component tests throughout the Dagster codebase.

## Core Testing Infrastructure

### `create_defs_folder_sandbox`

The foundation of component testing is `dagster.components.testing.create_defs_folder_sandbox`, which creates a temporary project structure that mimics a real Dagster project's defs folder.

```python
from dagster.components.testing import create_defs_folder_sandbox

with create_defs_folder_sandbox() as sandbox:
    # Test operations here
    pass
```

The sandbox provides:
- **Isolated environment**: Temporary directory structure with proper Python module setup
- **Module cleanup**: Automatically removes loaded modules from `sys.modules` on exit
- **Project structure**: Creates `<temp>/src/<project_name>/defs/` structure

### DefsFolderSandbox Methods

#### `scaffold_component()`
Creates a component instance in the sandbox using the component class's scaffolder:

```python
defs_path = sandbox.scaffold_component(
    component_cls=MyComponent,
    defs_path="my_component",  # Optional: defaults to random name
    scaffold_params={"param1": "value1"},  # Parameters for scaffolder
    component_body={"type": "...", "attributes": {...}}  # Override defs.yaml content
)
```

#### `load_component_and_build_defs()`
Loads and instantiates a component instance from a scaffolded path:

```python
with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
    assert isinstance(component, MyComponent)
    # Test component and definitions
```

#### `build_all_defs()`
Builds definitions for all component instances in the sandbox (useful for multi-component tests):

```python
with sandbox.build_all_defs() as defs:
    # Test integrated definitions
    pass
```

## Common Testing Patterns

### 1. Basic Component Class Scaffolding Test

Test that your component class's scaffolder works correctly:

```python
def test_scaffold_component():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(component_cls=MyComponent)
        assert (defs_path / "defs.yaml").exists()
        assert (defs_path / "expected_file.yaml").exists()  # Component-specific files
```

### 2. Component Class Loading and Asset Generation

Test that your component class loads correctly and generates expected assets:

```python
def test_basic_component_load():
    component_body = {
        "type": "my_package.MyComponent",
        "attributes": {
            "param1": "value1",
            "param2": "value2"
        }
    }

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=MyComponent,
            component_body=component_body
        )

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
            assert isinstance(component, MyComponent)

            # Test expected assets are created
            expected_keys = {AssetKey("asset1"), AssetKey("asset2")}
            assert defs.resolve_asset_graph().get_all_asset_keys() == expected_keys
```

### 3. Parameterized Component Class Testing

Use pytest parameterization to test different configurations of your component class:

```python
@pytest.mark.parametrize(
    "config, expected_assets",
    [
        ({"filter": "type1"}, 2),
        ({"filter": "type2"}, 5),
        ({"filter": None}, 10),
    ],
    ids=["type1_filter", "type2_filter", "no_filter"]
)
def test_component_filtering(config, expected_assets):
    component_body = {
        "type": "my_package.MyComponent",
        "attributes": config
    }

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=MyComponent,
            component_body=component_body
        )
        
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
            assert len(defs.resolve_asset_graph().get_all_asset_keys()) == expected_assets
```

### 4. Helper Context Managers

Create reusable setup functions for complex component configurations. This introduces indirection, so it's not always the best option,
but is useful when additional setup is needed such as environment variables or mocks that are more complex than just using the sandbox.

```python
@contextmanager
def setup_my_component(
    component_body: dict[str, Any],
    environment_vars: Optional[dict[str, str]] = None
) -> Iterator[tuple[MyComponent, Definitions]]:
    """Sets up a component with environment and returns component + defs."""
    env_vars = environment_vars or {}

    with (
        create_defs_folder_sandbox() as sandbox,
        environ(env_vars),  # Set environment variables
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=MyComponent,
            component_body=component_body
        )

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
            assert isinstance(component, MyComponent)
            yield component, defs
```

### 5. Multi-Component Integration Testing

Test components that depend on other components:

```python
def test_multi_component_integration():
    with create_defs_folder_sandbox() as sandbox:
        # Create connection component
        sandbox.scaffold_component(
            component_cls=ConnectionComponent,
            defs_path="connection",
            component_body={
                "type": "my_package.ConnectionComponent",
                "attributes": {"host": "localhost", "port": 5432}
            }
        )

        # Create execution component that references connection
        sandbox.scaffold_component(
            component_cls=ExecutionComponent,
            defs_path="execution",
            component_body={
                "type": "my_package.ExecutionComponent",
                "attributes": {
                    "connection": "{{ load_component_at_path('connection') }}"
                }
            }
        )

        with sandbox.build_all_defs() as defs:
            # Test that components work together
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()
            assert len(asset_keys) > 0
```

## Asset Translation Testing

For components that support asset attribute translation, inherit from `TestTranslation`:

```python
from dagster.components.testing import TestTranslation

class TestMyComponentTranslation(TestTranslation):
    def test_translation(
        self,
        attributes: Mapping[str, Any],  # Provided by TestTranslation fixture
        assertion: Callable[[AssetSpec], bool],  # Provided by TestTranslation fixture
        key_modifier: Optional[Callable[[AssetKey], AssetKey]]  # Provided by TestTranslation fixture
    ) -> None:
        component_body = {
            "type": "my_package.MyComponent",
            "attributes": {
                "base_config": "value",
                "translation": attributes  # Translation attributes from fixture
            }
        }

        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=MyComponent,
                component_body=component_body
            )
            
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                # Get the asset key that will be tested
                key = AssetKey("my_asset")
                if key_modifier:
                    key = key_modifier(key)

                assets_def = defs.resolve_assets_def(key)
                assert assertion(assets_def.get_asset_spec(key))
```

## Op Customization Testing

For components that support op customization, inherit from `TestOpCustomization`:

```python
from dagster.components.testing import TestOpCustomization

class TestMyComponentOpCustomization(TestOpCustomization):
    def test_op_customization(
        self,
        attributes: Mapping[str, Any],  # Op attributes like name, tags, etc.
        assertion: Callable[[OpSpec], bool]  # Assertion function for op spec
    ) -> None:
        component_body = {
            "type": "my_package.MyComponent",
            "attributes": {
                "replications": [{"op": attributes}]  # Component-specific structure
            }
        }

        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=MyComponent,
                component_body=component_body
            )
            
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                # Access the op spec in component-specific way
                op_spec = component.replications[0].op
                assert op_spec
                assert assertion(op_spec)
```

## Environment and Resource Testing

### Environment Variables

Use `dagster._utils.env.environ` for temporary environment setup:

```python
from dagster._utils.env import environ

def test_component_with_env():
    with (
        environ({"API_KEY": "test_key", "API_SECRET": "test_secret"}),
        setup_my_component(component_body) as (component, defs)
    ):
        # Component has access to environment variables
        pass
```

### Resource Mocking

Mock external resources for component testing:

```python
@mock.patch("external_service.connect", new_callable=create_mock_connector)
def test_component_with_mocked_resource(mock_connect):
    component_body = {
        "type": "my_package.MyComponent",
        "attributes": {"connection_config": "value"}
    }
    
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=MyComponent,
            component_body=component_body
        )
        
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
            # Execute component logic
            result = materialize([defs.get_assets_def("my_asset")])

            # Verify mock interactions
            mock_connect.assert_called_once_with(expected_params)
            assert result.success
```

## Component Execution Testing

### Direct Component Building

For simple unit-style tests, build component definitions directly:

```python
from dagster.components.core.tree import ComponentTree

def test_component_direct():
    component = MyComponent(param1="value1", param2="value2")
    context = ComponentTree.for_test().load_context
    defs = component.build_defs(context)

    # Test the definitions
    assert len(defs.get_all_asset_keys()) == expected_count
```

### Component Materialization

Test actual component execution:

```python
def test_component_execution():
    component_body = {
        "type": "my_package.MyComponent",
        "attributes": {"param": "value"}
    }
    
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=MyComponent,
            component_body=component_body
        )
        
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
            asset_def = defs.get_assets_def("my_asset")

            result = materialize([asset_def], resources=test_resources)
            assert result.success

            # Check materialization results
            materializations = result.get_asset_materialization_events()
            assert len(materializations) == 1
            assert "expected_metadata" in materializations[0].materialization.metadata
```

## File and Code Management

### Code Injection

Use `copy_code_to_file` to inject Python code into the sandbox:

```python
from dagster.components.testing import copy_code_to_file

def test_component_with_custom_code():
    with create_defs_folder_sandbox() as sandbox:
        # Define code to inject
        def code_to_copy():
            import dagster as dg

            def execute_fn(context) -> dg.MaterializeResult:
                return dg.MaterializeResult()

        # Copy code to sandbox
        copy_code_to_file(code_to_copy, sandbox.defs_folder_path / "execute.py")

        # Component can now reference this code
        component_body = {
            "type": "dagster.FunctionComponent",
            "attributes": {
                "execution": {"fn": ".execute.execute_fn"},
                "assets": [{"key": "my_asset"}]
            }
        }
```

### File Structure Setup

For components requiring specific file structures:

```python
import shutil

def test_component_with_files():
    with create_defs_folder_sandbox() as sandbox:
        # Copy required files into sandbox
        shutil.copytree(
            Path(__file__).parent / "test_files",
            sandbox.defs_folder_path / "test_files"
        )

        # Update component configuration to reference files
        component_body = {
            "attributes": {
                "config_path": "./test_files/config.yaml"
            }
        }
```

## Best Practices

1. **Use descriptive test names** that indicate what component behavior is being tested
2. **Group related tests** using helper functions and consistent naming
3. **Test both happy path and error cases** for component configurations
4. **Verify asset metadata** and other component-specific outputs
5. **Use parameterized tests** for testing multiple configurations efficiently
6. **Mock external dependencies** to ensure tests are deterministic and fast
7. **Test scaffolding separately** from runtime behavior when both are important
8. **Use environment context managers** to avoid test pollution
9. **Assert on specific asset keys and metadata** rather than just counts when possible
10. **Test component composition** when your component is designed to work with others

## Common Gotchas

- **Module cleanup**: The sandbox handles module cleanup, but be aware that component imports persist across tests
- **Environment isolation**: Use context managers for environment variables to avoid test interference
- **File paths**: Use absolute paths when working with files in the sandbox
- **Resource lifecycle**: Mock resources should be created per test to avoid state sharing
- **Component attributes**: Use `component_body` parameter to override scaffolded configurations rather than modifying files manually
