import inspect
from typing import Any, Union, get_type_hints

from dagster_airbyte import AirbyteDestination, AirbyteSource
from dagster_airbyte.managed.generated import destinations, sources


def instantiate(obj: Any) -> Any:
    """
    Utility that attempts to instantiate a class with dummy values for all of its parameters.
    """
    signature = get_type_hints(obj.__init__)

    inputs = {}
    for param_name, param_type in signature.items():
        if param_name == "self":
            continue

        inputs[param_name] = get_param_value(param_name, param_type)

    return obj(**inputs)


def get_param_value(param_name, param_type) -> Any:
    """
    Simple utility to generate an input for a given parameter name and type.
    """
    if param_name == "name":
        return "test_name"

    if param_type == str:
        return "foo"
    elif param_type == int:
        return 1
    elif param_type == bool:
        return True
    elif getattr(param_type, "__origin__", None) == Union:
        return get_param_value(param_name, param_type.__args__[0])
    elif getattr(param_type, "__origin__", None) == list:
        return [get_param_value(param_name, param_type.__args__[0])]
    elif inspect.isclass(param_type):
        return instantiate(param_type)
    else:
        raise Exception("Unhandled type: {}".format(param_type))


def test_destination_constructors():
    """
    Sanity check that we can instantiate all of the generated AirbyteDestination classes
    and that they produce a reasonable-looking configuration JSON.
    """
    for source, possible_class in inspect.getmembers(destinations):
        if source == "GeneratedAirbyteDestination":
            continue

        if inspect.isclass(possible_class):
            obj: AirbyteDestination = instantiate(possible_class)

            # Make sure that the name flows through correctly
            assert obj.name == "test_name"

            # Ensure that the top-level constructor params match the top-level config dict keys
            top_level_params = set(get_type_hints(obj.__init__).keys())
            top_level_params.remove("name")
            assert top_level_params == set(obj.destination_configuration.keys())


def test_source_constructors():
    """
    Sanity check that we can instantiate all of the generated AirbyteSource classes
    and that they produce a reasonable-looking configuration JSON.
    """
    for source, possible_class in inspect.getmembers(sources):
        if source == "GeneratedAirbyteSource":
            continue

        if inspect.isclass(possible_class):
            obj: AirbyteSource = instantiate(possible_class)

            # Make sure that the name flows through correctly
            assert obj.name == "test_name"

            # Ensure that the top-level constructor params match the top-level config dict keys
            top_level_params = set(get_type_hints(obj.__init__).keys())
            top_level_params.remove("name")
            assert top_level_params == set(obj.source_configuration.keys())
