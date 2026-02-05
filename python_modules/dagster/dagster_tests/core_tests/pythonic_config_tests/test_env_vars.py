import os

import dagster as dg
import pytest
from dagster import EnvVar
from dagster._core.test_utils import environ


def test_direct_use_env_var_ok() -> None:
    with environ({"A_STR": "foo"}):
        assert dg.EnvVar("A_STR").get_value() == "foo"
        assert dg.EnvVar("A_STR").get_value(default="bar") == "foo"

    if "A_NON_EXISTENT_VAR" in os.environ:
        del os.environ["A_NON_EXISTENT_VAR"]

    assert dg.EnvVar("A_NON_EXISTENT_VAR").get_value() is None
    assert dg.EnvVar("A_NON_EXISTENT_VAR").get_value(default="bar") == "bar"


def test_direct_use_int_env_var_ok() -> None:
    with environ({"AN_INT": "55"}):
        assert EnvVar.int("AN_INT").get_value() == 55
        assert EnvVar.int("AN_INT").get_value(default=10) == 55

    if "A_NON_EXISTENT_VAR" in os.environ:
        del os.environ["A_NON_EXISTENT_VAR"]

    assert EnvVar.int("A_NON_EXISTENT_VAR").get_value() is None
    assert EnvVar.int("A_NON_EXISTENT_VAR").get_value(default=100) == 100


def test_direct_use_env_var_err() -> None:
    with pytest.raises(
        RuntimeError,
        match=(
            r'Attempted to directly retrieve environment variable EnvVar\\("A_STR"\\). EnvVar defers'
            " resolution of the environment variable value until run time, and should only be used"
            " as input to Dagster config or resources.\n\n"
        ),
    ):
        str(dg.EnvVar("A_STR"))

    with pytest.raises(
        RuntimeError,
        match=(
            r'Attempted to directly retrieve environment variable EnvVar\\("A_STR"\\). EnvVar defers'
            " resolution of the environment variable value until run time, and should only be used"
            " as input to Dagster config or resources.\n\n"
        ),
    ):
        print(dg.EnvVar("A_STR"))  # noqa: T201


def test_direct_use_int_env_var_err() -> None:
    with pytest.raises(
        RuntimeError,
        match=(
            r'Attempted to directly retrieve environment variable IntEnvVar\\("AN_INT"\\). IntEnvVar'
            " defers resolution of the environment variable value until run time, and should only"
            " be used as input to Dagster config or resources."
        ),
    ):
        int(EnvVar.int("AN_INT"))

    with pytest.raises(
        RuntimeError,
        match=(
            r'Attempted to directly retrieve environment variable IntEnvVar\\("AN_INT"\\). IntEnvVar'
            " defers resolution of the environment variable value until run time, and should only"
            " be used as input to Dagster config or resources."
        ),
    ):
        print(EnvVar.int("AN_INT"))  # noqa: T201


def test_str_env_var() -> None:
    executed = {}

    class AStringConfig(dg.Config):
        a_str: str

    @dg.asset
    def a_string_asset(config: AStringConfig):
        assert config.a_str == "foo"
        executed["a_string_asset"] = True

    defs = dg.Definitions(assets=[a_string_asset])

    with environ({"A_STR": "foo"}):
        defs.resolve_implicit_global_asset_job_def().execute_in_process(
            run_config=dg.RunConfig(ops={"a_string_asset": AStringConfig(a_str=dg.EnvVar("A_STR"))})
        )
    assert executed["a_string_asset"]


def test_str_env_var_nested() -> None:
    executed = {}

    class AStringConfig(dg.Config):
        a_str: str

    class AnOuterConfig(dg.Config):
        inner: AStringConfig

    @dg.asset
    def a_string_asset(config: AnOuterConfig):
        assert config.inner.a_str == "bar"
        executed["a_string_asset"] = True

    defs = dg.Definitions(assets=[a_string_asset])

    with environ({"A_STR": "bar"}):
        defs.resolve_implicit_global_asset_job_def().execute_in_process(
            run_config=dg.RunConfig(
                ops={"a_string_asset": AnOuterConfig(inner=AStringConfig(a_str=dg.EnvVar("A_STR")))}
            )
        )
    assert executed["a_string_asset"]


def test_int_env_var() -> None:
    executed = {}

    class AnIntConfig(dg.Config):
        an_int: int

    @dg.asset
    def an_int_asset(config: AnIntConfig):
        assert config.an_int == 5
        executed["an_int_asset"] = True

    defs = dg.Definitions(assets=[an_int_asset])

    with environ({"AN_INT": "5"}):
        defs.resolve_implicit_global_asset_job_def().execute_in_process(
            run_config=dg.RunConfig(ops={"an_int_asset": AnIntConfig(an_int=EnvVar.int("AN_INT"))})
        )
    assert executed["an_int_asset"]


def test_int_env_var_nested() -> None:
    executed = {}

    class AnIntConfig(dg.Config):
        a_int: int

    class AnOuterConfig(dg.Config):
        inner: AnIntConfig

    @dg.asset
    def a_int_asset(config: AnOuterConfig):
        assert config.inner.a_int == 10
        executed["a_int_asset"] = True

    defs = dg.Definitions(assets=[a_int_asset])

    with environ({"AN_INT": "10"}):
        defs.resolve_implicit_global_asset_job_def().execute_in_process(
            run_config=dg.RunConfig(
                ops={"a_int_asset": AnOuterConfig(inner=AnIntConfig(a_int=EnvVar.int("AN_INT")))}
            )
        )
    assert executed["a_int_asset"]


def test_int_env_var_non_int_value() -> None:
    executed = {}

    class AnIntConfig(dg.Config):
        an_int: int

    @dg.asset
    def an_int_asset(config: AnIntConfig):
        assert config.an_int == 5
        executed["an_int_asset"] = True

    defs = dg.Definitions(assets=[an_int_asset])

    with environ({"AN_INT": "NOT_AN_INT"}):
        with pytest.raises(
            dg.DagsterInvalidConfigError,
            match=(r'Value stored in env variable "AN_INT" cannot be coerced into an int.'),
        ):
            defs.resolve_implicit_global_asset_job_def().execute_in_process(
                run_config=dg.RunConfig(
                    ops={"an_int_asset": AnIntConfig(an_int=EnvVar.int("AN_INT"))}
                )
            )
    assert len(executed) == 0


def test_str_env_var_default() -> None:
    executed = {}

    class AStringConfig(dg.Config):
        a_str: str = dg.EnvVar("A_STR")

    @dg.asset
    def a_string_asset(config: AStringConfig):
        assert config.a_str == "foo"
        executed["a_string_asset"] = True

    defs = dg.Definitions(assets=[a_string_asset])

    with environ({"A_STR": "foo"}):
        defs.resolve_implicit_global_asset_job_def().execute_in_process(
            run_config=dg.RunConfig(ops={"a_string_asset": AStringConfig()})
        )
    assert executed["a_string_asset"]


def test_int_env_var_default() -> None:
    executed = {}

    class AnIntConfig(dg.Config):
        an_int: int = EnvVar.int("AN_INT")

    @dg.asset
    def an_int_asset(config: AnIntConfig):
        assert config.an_int == 55
        executed["an_int_asset"] = True

    defs = dg.Definitions(assets=[an_int_asset])

    with environ({"AN_INT": "55"}):
        defs.resolve_implicit_global_asset_job_def().execute_in_process(
            run_config=dg.RunConfig(ops={"an_int_asset": AnIntConfig()})
        )
    assert executed["an_int_asset"]
