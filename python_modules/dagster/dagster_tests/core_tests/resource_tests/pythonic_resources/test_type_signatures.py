import os
import re
import subprocess
import tempfile
from typing import List

import pytest


def get_pyright_reveal_type_output(filename) -> List[str]:
    stdout = subprocess.check_output(["pyright", filename]).decode("utf-8")
    match = re.findall(r'Type of "(?:[^"]+)" is "([^"]+)"', stdout)
    assert match
    return match


def get_mypy_type_output(filename) -> List[str]:
    stdout = subprocess.check_output(["mypy", filename]).decode("utf-8")
    match = re.findall(r'note: Revealed type is "([^"]+)"', stdout)
    assert match
    return match


# you can specify the -m "typesignature" flag to run these tests, they're
# slow so we don't want to run them by default
@pytest.mark.typesignature
def test_type_signatures_constructor_nested_resource():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster import ConfigurableResource

class InnerResource(ConfigurableResource):
    a_string: str

class OuterResource(ConfigurableResource):
    inner: InnerResource
    a_bool: bool

reveal_type(InnerResource.__init__)
reveal_type(OuterResource.__init__)

my_outer = OuterResource(inner=InnerResource(a_string="foo"), a_bool=True)
reveal_type(my_outer.inner)
"""
            )

        pyright_out = get_pyright_reveal_type_output(filename)
        mypy_out = get_mypy_type_output(filename)

        # Ensure constructor signature is correct (mypy doesn't yet support Pydantic model constructor type hints)
        assert pyright_out[0] == "(self: InnerResource, *, a_string: str) -> None"
        assert (
            pyright_out[1]
            == "(self: OuterResource, *, inner: InnerResource | PartialResource[InnerResource],"
            " a_bool: bool) -> None"
        )

        # Ensure that the retrieved type is the same as the type of the resource (no partial)
        assert pyright_out[2] == "InnerResource"
        assert mypy_out[2] == "test.InnerResource"


@pytest.mark.typesignature
def test_type_signatures_config_at_launch():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster import ConfigurableResource

class MyResource(ConfigurableResource):
    a_string: str

reveal_type(MyResource.configure_at_launch())
"""
            )

        pyright_out = get_pyright_reveal_type_output(filename)
        mypy_out = get_mypy_type_output(filename)

        # Ensure partial resource is correctly parameterized
        assert pyright_out[0] == "PartialResource[MyResource]"
        assert mypy_out[0].endswith("PartialResource[test.MyResource]")


@pytest.mark.typesignature
def test_type_signatures_constructor_resource_dependency():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster import ConfigurableResource, ResourceDependency

class StringDependentResource(ConfigurableResource):
    a_string: ResourceDependency[str]

reveal_type(StringDependentResource.__init__)

my_str_resource = StringDependentResource(a_string="foo")
reveal_type(my_str_resource.a_string)
"""
            )

        pyright_out = get_pyright_reveal_type_output(filename)
        mypy_out = get_mypy_type_output(filename)

        # Ensure constructor signature supports str Resource, PartialResource, raw str, or a
        # resource function that returns a str
        assert (
            pyright_out[0]
            == "(self: StringDependentResource, *, a_string: ConfigurableResourceFactory[str] |"
            " PartialResource[str] | ResourceDefinition | str) -> None"
        )

        # Ensure that the retrieved type is str
        assert pyright_out[1] == "str"
        assert mypy_out[1] == "builtins.str"


@pytest.mark.typesignature
def test_type_signatures_alias():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster import ConfigurableResource
from pydantic import Field

class ResourceWithAlias(ConfigurableResource):
    _schema: str = Field(alias="schema")

reveal_type(ResourceWithAlias.__init__)

my_resource = ResourceWithAlias(schema="foo")
"""
            )

        pyright_out = get_pyright_reveal_type_output(filename)

        # Ensure constructor signature shows schema as the alias
        assert pyright_out[0] == "(self: ResourceWithAlias, *, schema: str) -> None"
