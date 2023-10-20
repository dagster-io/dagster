from inspect import signature
from typing import List, Type

from dagster._core.definitions import asset_checks
from dagster._core.definitions.asset_checks import (
    AssetChecksDefinition,
    AssetChecksDefinitionProps,
    IDefinitionPropsClassMatchesInit,
)
from dagster._utils.test import get_all_direct_subclasses_of_marker


def test_adherence_of_all_idef_props_class_matches_init() -> None:
    def_types: List[Type] = get_all_direct_subclasses_of_marker(
        IDefinitionPropsClassMatchesInit, module=asset_checks
    )

    hard_coded_list = [
        (AssetChecksDefinition, AssetChecksDefinitionProps),
    ]

    # keep hard_coded_list up-to-date with all subclasses of IDefinitionPropsClassMatchesInit
    assert set([def_type.__name__ for def_type in def_types]) == set(
        [entry[0].__name__ for entry in hard_coded_list]
    ), (
        "You likely added a subclass of IDefinitionPropsClassMatchesInit without adding it to the"
        " hard_coded_list"
    )

    for def_type, props_type in hard_coded_list:
        init_params = signature(def_type.__init__).parameters
        init_param_names_minus_self = set(init_params.keys()) - set(["self"])
        named_tuple_fields = set(props_type._fields)
        assert init_param_names_minus_self == named_tuple_fields, (
            f"You have added either added a field to {props_type.__name__} or removed a parameter"
            f" from {def_type.__name__}.__init__. They must remain in sync"
        )
