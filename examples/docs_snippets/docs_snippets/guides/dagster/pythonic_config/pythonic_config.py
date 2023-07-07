# ruff: isort: skip_file


from typing import Dict, List


class Engine:
    def execute(self, query: str):
        ...


def get_engine(connection_url: str) -> Engine:
    return Engine()


def basic_resource_config() -> None:
    # start_basic_resource_config

    from dagster import op, ConfigurableResource

    class MyDatabaseResource(ConfigurableResource):
        connection_url: str

        def query(self, query: str):
            return get_engine(self.connection_url).execute(query)

    # end_basic_resource_config


def permissive_schema_config() -> None:
    # start_permissive_schema_config

    from dagster import asset, PermissiveConfig
    from typing import Optional
    import requests

    class FilterConfig(PermissiveConfig):
        title: Optional[str] = None
        description: Optional[str] = None

    @asset
    def filtered_listings(config: FilterConfig):
        # extract all config fields, including those not defined in the schema
        url_params = config.dict()
        return requests.get("https://my-api.com/listings", params=url_params).json()

    # can pass in any fields, including those not defined in the schema
    filtered_listings(FilterConfig(title="hotel", beds=4))  # type: ignore
    # end_permissive_schema_config


def execute_with_config() -> None:
    # start_basic_op_config

    from dagster import op, Config

    class MyOpConfig(Config):
        person_name: str

    @op
    def print_greeting(config: MyOpConfig):
        print(f"hello {config.person_name}")  # noqa: T201

    # end_basic_op_config

    # start_basic_asset_config

    from dagster import asset, Config

    class MyAssetConfig(Config):
        person_name: str

    @asset
    def greeting(config: MyAssetConfig) -> str:
        return f"hello {config.person_name}"

    # end_basic_asset_config

    # start_execute_with_config
    from dagster import job, materialize, op, RunConfig

    @job
    def greeting_job():
        print_greeting()

    job_result = greeting_job.execute_in_process(
        run_config=RunConfig({"print_greeting": MyOpConfig(person_name="Alice")})
    )

    asset_result = materialize(
        [greeting],
        run_config=RunConfig({"greeting": MyAssetConfig(person_name="Alice")}),
    )

    # end_execute_with_config

    # start_execute_with_config_envvar
    from dagster import job, materialize, op, RunConfig, EnvVar

    job_result = greeting_job.execute_in_process(
        run_config=RunConfig(
            {"print_greeting": MyOpConfig(person_name=EnvVar("PERSON_NAME"))}
        )
    )

    asset_result = materialize(
        [greeting],
        run_config=RunConfig(
            {"greeting": MyAssetConfig(person_name=EnvVar("PERSON_NAME"))}
        ),
    )

    # end_execute_with_config_envvar


def basic_data_structures_config() -> None:
    # start_basic_data_structures_config
    from dagster import Config, materialize, asset, RunConfig
    from typing import List, Dict

    class MyDataStructuresConfig(Config):
        user_names: List[str]
        user_scores: Dict[str, int]

    @asset
    def scoreboard(config: MyDataStructuresConfig):
        ...

    result = materialize(
        [scoreboard],
        run_config=RunConfig(
            {
                "scoreboard": MyDataStructuresConfig(
                    user_names=["Alice", "Bob"],
                    user_scores={"Alice": 10, "Bob": 20},
                )
            }
        ),
    )

    # end_basic_data_structures_config


def nested_schema_config() -> None:
    # start_nested_schema_config
    from dagster import asset, materialize, Config, RunConfig
    from typing import Dict

    class UserData(Config):
        age: int
        email: str
        profile_picture_url: str

    class MyNestedConfig(Config):
        user_data: Dict[str, UserData]

    @asset
    def average_age(config: MyNestedConfig):
        ...

    result = materialize(
        [average_age],
        run_config=RunConfig(
            {
                "average_age": MyNestedConfig(
                    user_data={
                        "Alice": UserData(age=10, email="alice@gmail.com", profile_picture_url=...),  # type: ignore
                        "Bob": UserData(age=20, email="bob@gmail.com", profile_picture_url=...),  # type: ignore
                    }
                )
            }
        ),
    )

    # end_nested_schema_config


def union_schema_config() -> None:
    # start_union_schema_config

    from dagster import asset, materialize, Config, RunConfig
    from pydantic import Field
    from typing import Union
    from typing_extensions import Literal

    class Cat(Config):
        pet_type: Literal["cat"] = "cat"
        meows: int

    class Dog(Config):
        pet_type: Literal["dog"] = "dog"
        barks: float

    class ConfigWithUnion(Config):
        pet: Union[Cat, Dog] = Field(discriminator="pet_type")

    @asset
    def pet_stats(config: ConfigWithUnion):
        if isinstance(config.pet, Cat):
            return f"Cat meows {config.pet.meows} times"
        else:
            return f"Dog barks {config.pet.barks} times"

    result = materialize(
        [pet_stats],
        run_config=RunConfig(
            {
                "pet_stats": ConfigWithUnion(
                    pet=Cat(meows=10),
                )
            }
        ),
    )
    # end_union_schema_config


def metadata_config() -> None:
    #  start_metadata_config
    from dagster import Config
    from pydantic import Field

    class MyMetadataConfig(Config):
        person_name: str = Field(description="The name of the person to greet")
        age: int = Field(gt=0, lt=100, description="The age of the person to greet")

    # errors, since age is not in the valid range!
    MyMetadataConfig(person_name="Alice", age=200)

    # end_metadata_config


def optional_config() -> None:
    # start_optional_config

    from typing import Optional
    from dagster import asset, Config, materialize, RunConfig
    from pydantic import Field

    class MyAssetConfig(Config):
        person_name: Optional[str] = None

        # can pass default to pydantic.Field to attach metadata to the field
        greeting_phrase: str = Field(
            default="hello", description="The greeting phrase to use."
        )

    @asset
    def greeting(config: MyAssetConfig) -> str:
        if config.person_name:
            return f"{config.greeting_phrase} {config.person_name}"
        else:
            return config.greeting_phrase

    asset_result = materialize(
        [greeting],
        run_config=RunConfig({"greeting": MyAssetConfig()}),
    )

    # end_optional_config


def execute_with_bad_config() -> None:
    from dagster import op, job, materialize, Config, RunConfig

    class MyOpConfig(Config):
        person_name: str

    @op
    def print_greeting(config: MyOpConfig):
        print(f"hello {config.person_name}")  # noqa: T201

    from dagster import asset, Config

    class MyAssetConfig(Config):
        person_name: str

    @asset
    def greeting(config: MyAssetConfig) -> str:
        return f"hello {config.person_name}"

    # start_execute_with_bad_config

    @job
    def greeting_job():
        print_greeting()

    op_result = greeting_job.execute_in_process(
        run_config=RunConfig({"print_greeting": MyOpConfig(nonexistent_config_value=1)}),  # type: ignore
    )

    asset_result = materialize(
        [greeting],
        run_config=RunConfig({"greeting": MyAssetConfig(nonexistent_config_value=1)}),  # type: ignore
    )

    # end_execute_with_bad_config


def enum_schema_config() -> None:
    # start_enum_schema_config

    from dagster import Config, RunConfig, op, job
    from enum import Enum

    class UserPermissions(Enum):
        GUEST = "guest"
        MEMBER = "member"
        ADMIN = "admin"

    class ProcessUsersConfig(Config):
        users_list: Dict[str, UserPermissions]

    @op
    def process_users(config: ProcessUsersConfig):
        for user, permission in config.users_list.items():
            if permission == UserPermissions.ADMIN:
                print(f"{user} is an admin")  # noqa: T201

    @job
    def process_users_job():
        process_users()

    op_result = process_users_job.execute_in_process(
        run_config=RunConfig(
            {
                "process_users": ProcessUsersConfig(
                    users_list={
                        "Bob": UserPermissions.GUEST,
                        "Alice": UserPermissions.ADMIN,
                    }
                )
            }
        ),
    )
    # end_enum_schema_config


def validated_schema_config() -> None:
    # start_validated_schema_config

    from dagster import Config, RunConfig, op, job
    from pydantic import validator

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

    # Input is valid, so this will work
    op_result = greet_user_job.execute_in_process(
        run_config=RunConfig(
            {"greet_user": UserConfig(name="Alice Smith", username="alice123")}
        ),
    )

    # Name has no space, so this will fail
    op_result = greet_user_job.execute_in_process(
        run_config=RunConfig(
            {"greet_user": UserConfig(name="John", username="johndoe44")}
        ),
    )

    # end_validated_schema_config


def required_config() -> None:
    # start_required_config
    from typing import Optional, Callable
    from dagster import asset, Config
    from pydantic import Field

    class MyAssetConfig(Config):
        # ellipsis indicates that even though the type is Optional,
        # an input is required
        person_first_name: Optional[str] = ...  # type: ignore

        # ellipsis can also be used with pydantic.Field to attach metadata
        person_last_name: Optional[Callable] = Field(
            default=..., description="The last name of the person to greet"
        )

    @asset
    def goodbye(config: MyAssetConfig) -> str:
        full_name = f"{config.person_first_name} {config.person_last_name}".strip()
        if full_name:
            return f"Goodbye, {full_name}"
        else:
            return "Goodbye"

    # errors, since person_first_name and person_last_name are required
    goodbye(MyAssetConfig())

    # works, since both person_first_name and person_last_name are provided
    goodbye(MyAssetConfig(person_first_name="Alice", person_last_name=None))

    # end_required_config
