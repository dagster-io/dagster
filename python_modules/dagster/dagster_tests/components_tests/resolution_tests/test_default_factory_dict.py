from dataclasses import dataclass, field

import dagster as dg


def test_dataclass_default_factory_dict():
    @dataclass
    class MyThing(dg.Resolvable):
        items: dict = field(default_factory=dict)

    # empty yaml should produce an instance with the default dict
    t = MyThing.resolve_from_yaml("")
    assert isinstance(t.items, dict)
    assert t.items == {}

    # explicit yaml should override the default
    t2 = MyThing.resolve_from_yaml(
        """
items:
  a: 1
"""
    )
    assert t2.items == {"a": 1}
