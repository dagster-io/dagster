from dataclasses import dataclass

import pytest
from dagster._utils.env import environ
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.errors import ResolutionException


def test_env():
    with environ({"MY_ENV_VAR": "my_value"}):

        @dataclass
        class MyNewThing(Resolvable):
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
        class MyNewThing(Resolvable):
            name: str

        assert (
            MyNewThing.resolve_from_yaml("""
    name: "{{ env.MY_ENV_VAR }}"
    """).name
            == "my_value"
        )


def test_env_indexing():
    with environ({"MY_ENV_VAR": "my_value"}):

        @dataclass
        class MyNewThing(Resolvable):
            name: str

        with pytest.raises(
            ResolutionException,
            match=r".*To access environment variables, use dot access or the `env` function, e.g. `env\.MY_ENV_VAR` or `env\('MY_ENV_VAR'\)`.*",
        ):
            MyNewThing.resolve_from_yaml("""
    name: "{{ env['MY_ENV_VAR'] }}"
    """)
