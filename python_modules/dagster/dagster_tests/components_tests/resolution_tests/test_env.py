import os
from dataclasses import dataclass

import dagster as dg
import pytest
from dagster._utils.env import environ
from dagster.components.resolved.errors import ResolutionException


def test_env():
    with environ({"MY_ENV_VAR": "my_value"}):

        @dataclass
        class MyNewThing(dg.Resolvable):
            name: str

        assert (
            MyNewThing.resolve_from_yaml("""
    name: "{{ env('MY_ENV_VAR') }}"
    """).name
            == "my_value"
        )


def test_env_dot_access():
    with environ({"MY_ENV_VAR": "my_value"}):

        @dataclass
        class MyNewThing(dg.Resolvable):
            name: str

        assert (
            MyNewThing.resolve_from_yaml("""
    name: "{{ env.MY_ENV_VAR }}"
    """).name
            == "my_value"
        )


def test_env_with_and_without_default():
    if os.environ.get("MY_ENV_VAR"):
        del os.environ["MY_ENV_VAR"]

    @dataclass
    class MyNewThing(dg.Resolvable):
        name: str

    with pytest.raises(
        ResolutionException,
        match=r".*Environment variable MY_ENV_VAR is not set and no default value was provided. To provide a default value, use e.g. `env\('MY_ENV_VAR', 'default_value'\)`.*",
    ):
        assert (
            MyNewThing.resolve_from_yaml("""
    name: "{{ env('MY_ENV_VAR') }}"
    """).name
            == "my_value"
        )

    assert (
        MyNewThing.resolve_from_yaml("""
    name: "{{ env('MY_ENV_VAR', 'default_value') }}"
    """).name
        == "default_value"
    )


def test_env_indexing():
    with environ({"MY_ENV_VAR": "my_value"}):

        @dataclass
        class MyNewThing(dg.Resolvable):
            name: str

        with pytest.raises(
            ResolutionException,
            match=r".*To access environment variables, use dot access or the `env` function, e.g. `env\.MY_ENV_VAR` or `env\('MY_ENV_VAR'\)`.*",
        ):
            MyNewThing.resolve_from_yaml("""
    name: "{{ env['MY_ENV_VAR'] }}"
    """)
