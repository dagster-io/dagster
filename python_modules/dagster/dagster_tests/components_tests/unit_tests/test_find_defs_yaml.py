from pathlib import Path

from dagster.components.core.defs_module import find_defs_or_component_yaml


def test_find_defs_or_component_yaml(tmp_path: Path):
    # Empty dir → None
    assert find_defs_or_component_yaml(tmp_path) is None

    # Falls back to deprecated component.yaml when no defs.* exists
    component_yaml = tmp_path / "component.yaml"
    component_yaml.write_text("type: a\n", encoding="utf-8")
    assert find_defs_or_component_yaml(tmp_path) == component_yaml

    # defs.yml takes precedence over component.yaml
    defs_yml = tmp_path / "defs.yml"
    defs_yml.write_text("type: b\n", encoding="utf-8")
    assert find_defs_or_component_yaml(tmp_path) == defs_yml

    # defs.yaml takes precedence over defs.yml (and component.yaml)
    defs_yaml = tmp_path / "defs.yaml"
    defs_yaml.write_text("type: c\n", encoding="utf-8")
    assert find_defs_or_component_yaml(tmp_path) == defs_yaml
