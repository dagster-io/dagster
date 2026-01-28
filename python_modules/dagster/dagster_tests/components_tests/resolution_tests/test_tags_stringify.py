from dagster.components.resolved.core_models import SharedAssetKwargs


def test_tags_are_strings_even_when_native_template_coerces_types():
    yaml_str = """
tags:
  num: "{{ 512 }}"
  obj: "{{ {'cpu': '1024'} }}"
  plain: "512"
"""
    resolved = SharedAssetKwargs.resolve_from_yaml(yaml_str)

    assert resolved.tags["num"] == "512"
    assert resolved.tags["obj"] == '{"cpu": "1024"}'
    assert resolved.tags["plain"] == "512"
