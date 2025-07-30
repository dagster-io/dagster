from pathlib import Path

from dagster.components.core.component_tree import ComponentTreeDependencies
from dagster.components.core.defs_module import ComponentPath


def test_get_load_dependents_of_component_empty():
    """Test that get_load_dependents_of_component returns empty list when no dependencies exist."""
    deps = ComponentTreeDependencies()
    defs_module_path = Path("/project/defs")

    component_path = ComponentPath(file_path=Path("some_component"), instance_key=None)
    dependents = deps.get_load_dependents_of_component(defs_module_path, component_path)

    assert dependents == []


def test_get_load_dependents_of_component_simple():
    """Test basic dependency chain: A depends on B, so B's dependents should include A."""
    deps = ComponentTreeDependencies()
    defs_module_path = Path("/project/defs")

    # Set up: component_a depends on component_b
    component_a = ComponentPath(file_path=Path("component_a"), instance_key=None)
    component_b = ComponentPath(file_path=Path("component_b"), instance_key=None)

    deps.mark_component_load_dependency(defs_module_path, component_a, component_b)

    # component_b should have component_a as a dependent
    dependents_of_b = deps.get_load_dependents_of_component(defs_module_path, component_b)
    assert component_a in dependents_of_b
    assert len(dependents_of_b) == 1

    # component_a should have no dependents
    dependents_of_a = deps.get_load_dependents_of_component(defs_module_path, component_a)
    assert dependents_of_a == []


def test_get_load_dependents_of_component_multiple_dependents():
    """Test multiple components depending on the same component."""
    deps = ComponentTreeDependencies()
    defs_module_path = Path("/project/defs")

    # Set up: both component_a and component_c depend on component_b
    component_a = ComponentPath(file_path=Path("component_a"), instance_key=None)
    component_b = ComponentPath(file_path=Path("component_b"), instance_key=None)
    component_c = ComponentPath(file_path=Path("component_c"), instance_key=None)

    deps.mark_component_load_dependency(defs_module_path, component_a, component_b)
    deps.mark_component_load_dependency(defs_module_path, component_c, component_b)

    # component_b should have both component_a and component_c as dependents
    dependents_of_b = deps.get_load_dependents_of_component(defs_module_path, component_b)
    assert component_a in dependents_of_b
    assert component_c in dependents_of_b
    assert len(dependents_of_b) == 2


def test_get_load_dependents_of_component_transitive_dependencies():
    """Test transitive dependency chain: A -> B -> C."""
    deps = ComponentTreeDependencies()
    defs_module_path = Path("/project/defs")

    # Set up: component_a depends on component_b, component_b depends on component_c
    component_a = ComponentPath(file_path=Path("component_a"), instance_key=None)
    component_b = ComponentPath(file_path=Path("component_b"), instance_key=None)
    component_c = ComponentPath(file_path=Path("component_c"), instance_key=None)

    deps.mark_component_load_dependency(defs_module_path, component_a, component_b)
    deps.mark_component_load_dependency(defs_module_path, component_b, component_c)

    # Test all transitive dependents - C should have both B and A as dependents
    dependents_of_c = deps.get_load_dependents_of_component(defs_module_path, component_c)
    assert component_b in dependents_of_c
    assert component_a in dependents_of_c
    assert len(dependents_of_c) == 2
    # B should come before A in topological order (B is direct dependent, A is transitive)
    assert dependents_of_c.index(component_b) < dependents_of_c.index(component_a)

    # B should only have A as dependent
    dependents_of_b = deps.get_load_dependents_of_component(defs_module_path, component_b)
    assert component_a in dependents_of_b
    assert len(dependents_of_b) == 1


def test_get_load_dependents_of_component_with_instance_keys():
    """Test dependencies with instance keys (for composite components)."""
    deps = ComponentTreeDependencies()
    defs_module_path = Path("/project/defs")

    # Set up: component_a depends on component_b with instance key
    component_a = ComponentPath(file_path=Path("component_a"), instance_key=None)
    component_b_instance_0 = ComponentPath(file_path=Path("component_b"), instance_key=0)
    component_b_instance_1 = ComponentPath(file_path=Path("component_b"), instance_key=1)

    deps.mark_component_load_dependency(defs_module_path, component_a, component_b_instance_0)

    # Only instance 0 should have dependents
    dependents_of_b_0 = deps.get_load_dependents_of_component(
        defs_module_path, component_b_instance_0
    )
    assert component_a in dependents_of_b_0
    assert len(dependents_of_b_0) == 1

    # Instance 1 should have no dependents
    dependents_of_b_1 = deps.get_load_dependents_of_component(
        defs_module_path, component_b_instance_1
    )
    assert dependents_of_b_1 == []


def test_get_load_dependents_topological_ordering():
    """Test that the method returns topologically sorted transitive dependents.

    Diamond dependency pattern:
    A -> B -> D
    A -> C -> D
    So D's transitive dependents should be: [B, C, A] (in topological order)
    """
    deps = ComponentTreeDependencies()
    defs_module_path = Path("/project/defs")

    # Set up a diamond dependency pattern:
    # A -> B -> D
    # A -> C -> D
    component_a = ComponentPath(file_path=Path("component_a"), instance_key=None)
    component_b = ComponentPath(file_path=Path("component_b"), instance_key=None)
    component_c = ComponentPath(file_path=Path("component_c"), instance_key=None)
    component_d = ComponentPath(file_path=Path("component_d"), instance_key=None)

    deps.mark_component_load_dependency(defs_module_path, component_a, component_b)
    deps.mark_component_load_dependency(defs_module_path, component_a, component_c)
    deps.mark_component_load_dependency(defs_module_path, component_b, component_d)
    deps.mark_component_load_dependency(defs_module_path, component_c, component_d)

    # D should have all transitive dependents: B, C, A
    dependents_of_d = deps.get_load_dependents_of_component(defs_module_path, component_d)
    assert component_b in dependents_of_d
    assert component_c in dependents_of_d
    assert component_a in dependents_of_d
    assert len(dependents_of_d) == 3

    # Both B and C should come before A in topological order
    assert dependents_of_d.index(component_b) < dependents_of_d.index(component_a)
    assert dependents_of_d.index(component_c) < dependents_of_d.index(component_a)


def test_get_load_dependents_of_component_nonexistent():
    """Test querying dependents of a component that doesn't exist in dependencies."""
    deps = ComponentTreeDependencies()
    defs_module_path = Path("/project/defs")

    # Set up some dependencies but not for the component we'll query
    component_a = ComponentPath(file_path=Path("component_a"), instance_key=None)
    component_b = ComponentPath(file_path=Path("component_b"), instance_key=None)
    component_c = ComponentPath(file_path=Path("component_c"), instance_key=None)

    deps.mark_component_load_dependency(defs_module_path, component_a, component_b)

    # Query dependents of component_c which has no dependencies
    dependents_of_c = deps.get_load_dependents_of_component(defs_module_path, component_c)
    assert dependents_of_c == []
