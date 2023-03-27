import pytest
from dagster import job, op
from dagster._config.structured_config import Config
from pydantic import ValidationError, validator


def test_validators_basic() -> None:
    # showcase that Pydantic validators work as expected

    class UserConfig(Config):
        name: str
        username: str

        @validator("name")
        def name_must_contain_space(cls, v):
            if " " not in v:
                raise ValueError("must contain a space")
            return v.title()

        @validator("username")
        def username_alphanumeric(cls, v):
            assert v.isalnum(), "must be alphanumeric"
            return v

    executed = {}

    @op
    def greet_user(config: UserConfig) -> None:
        print(f"Hello {config.name}!")  # noqa: T201
        executed["greet_user"] = True

    @job
    def greet_user_job() -> None:
        greet_user()

    # Ensure construction-time validation works
    UserConfig(name="Arthur Miller", username="arthur")
    with pytest.raises(ValidationError, match="must be alphanumeric"):
        UserConfig(name="Arthur Miller", username="arthur invalid")
    with pytest.raises(ValidationError, match="must contain a space"):
        UserConfig(name="Arthur", username="arthur")

    # Ensure execution-time validation works
    assert greet_user_job.execute_in_process(
        {"ops": {"greet_user": {"config": {"name": "Arthur Miller", "username": "arthur"}}}}
    ).success
    assert executed["greet_user"]

    executed.clear()
    with pytest.raises(ValidationError, match="must be alphanumeric"):
        greet_user_job.execute_in_process(
            {
                "ops": {
                    "greet_user": {
                        "config": {"name": "Arthur Miller", "username": "arthur invalid"}
                    }
                }
            }
        )
    assert not executed
    with pytest.raises(ValidationError, match="must contain a space"):
        greet_user_job.execute_in_process(
            {"ops": {"greet_user": {"config": {"name": "Arthur", "username": "arthur"}}}}
        )
    assert not executed
