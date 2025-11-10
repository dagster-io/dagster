# ruff: isort: skip_file


class Engine:
    def execute(self, query: str): ...


def get_engine(connection_url: str) -> Engine:
    return Engine()


def basic_resource_config() -> None:
    # start_basic_resource_config

    import dagster as dg

    class MyDatabaseResource(dg.ConfigurableResource):
        connection_url: str

        def query(self, query: str):
            return get_engine(self.connection_url).execute(query)

    # end_basic_resource_config


def permissive_schema_config() -> None:
    # start_permissive_schema_config

    import dagster as dg
    from typing import Optional
    import requests

    class FilterConfig(dg.PermissiveConfig):
        title: Optional[str] = None
        description: Optional[str] = None

    @dg.asset
    def filtered_listings(config: FilterConfig):
        # extract all config fields, including those not defined in the schema
        url_params = config.dict()
        return requests.get("https://my-api.com/listings", params=url_params).json()

    # can pass in any fields, including those not defined in the schema
    filtered_listings(FilterConfig(title="hotel", beds=4))  # type: ignore
    # end_permissive_schema_config


def execute_with_config() -> None:
    # start_basic_op_config

    import dagster as dg

    class MyOpConfig(dg.Config):
        person_name: str

    @dg.op
    def print_greeting(config: MyOpConfig):
        print(f"hello {config.person_name}")  # noqa: T201

    # end_basic_op_config

    # start_basic_asset_config

    import dagster as dg

    class MyAssetConfig(dg.Config):
        person_name: str

    @dg.asset
    def greeting(config: MyAssetConfig) -> str:
        return f"hello {config.person_name}"

    # end_basic_asset_config

    # start_execute_with_config
    import dagster as dg

    @dg.job
    def greeting_job():
        print_greeting()

    job_result = greeting_job.execute_in_process(
        run_config=dg.RunConfig({"print_greeting": MyOpConfig(person_name="Alice")})
    )

    asset_result = dg.materialize(
        [greeting],
        run_config=dg.RunConfig({"greeting": MyAssetConfig(person_name="Alice")}),
    )

    # end_execute_with_config

    # start_execute_with_config_envvar
    import dagster as dg

    job_result = greeting_job.execute_in_process(
        run_config=dg.RunConfig(
            {"print_greeting": MyOpConfig(person_name=dg.EnvVar("PERSON_NAME"))}
        )
    )

    asset_result = dg.materialize(
        [greeting],
        run_config=dg.RunConfig(
            {"greeting": MyAssetConfig(person_name=dg.EnvVar("PERSON_NAME"))}
        ),
    )

    # end_execute_with_config_envvar


def basic_data_structures_config() -> None:
    # start_basic_data_structures_config
    import dagster as dg

    class MyDataStructuresConfig(dg.Config):
        user_names: list[str]
        user_scores: dict[str, int]

    @dg.asset
    def scoreboard(config: MyDataStructuresConfig): ...

    result = dg.materialize(
        [scoreboard],
        run_config=dg.RunConfig(
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
    import dagster as dg

    class UserData(dg.Config):
        age: int
        email: str
        profile_picture_url: str

    class MyNestedConfig(dg.Config):
        user_data: dict[str, UserData]

    @dg.asset
    def average_age(config: MyNestedConfig): ...

    result = dg.materialize(
        [average_age],
        run_config=dg.RunConfig(
            {
                "average_age": MyNestedConfig(
                    user_data={
                        "Alice": UserData(
                            age=10,
                            email="alice@gmail.com",
                            profile_picture_url=...,
                        ),
                        "Bob": UserData(
                            age=20,
                            email="bob@gmail.com",
                            profile_picture_url=...,
                        ),
                    }
                )
            }
        ),
    )

    # end_nested_schema_config


def union_schema_config() -> None:
    # start_union_schema_config

    import dagster as dg
    from pydantic import Field
    from typing import Union
    from typing import Literal

    class Cat(dg.Config):
        pet_type: Literal["cat"] = "cat"
        meows: int

    class Dog(dg.Config):
        pet_type: Literal["dog"] = "dog"
        barks: float

    class ConfigWithUnion(dg.Config):
        pet: Union[Cat, Dog] = Field(discriminator="pet_type")

    @dg.asset
    def pet_stats(config: ConfigWithUnion):
        if isinstance(config.pet, Cat):
            return f"Cat meows {config.pet.meows} times"
        else:
            return f"Dog barks {config.pet.barks} times"

    result = dg.materialize(
        [pet_stats],
        run_config=dg.RunConfig(
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
    import dagster as dg
    from pydantic import Field

    class MyMetadataConfig(dg.Config):
        person_name: str = Field(description="The name of the person to greet")
        age: int = Field(gt=0, lt=100, description="The age of the person to greet")

    # errors, since age is not in the valid range!
    MyMetadataConfig(person_name="Alice", age=200)

    # end_metadata_config


def optional_config() -> None:
    # start_optional_config

    from typing import Optional
    import dagster as dg
    from pydantic import Field

    class MyAssetConfig(dg.Config):
        person_name: Optional[str] = None

        # can pass default to pydantic.Field to attach metadata to the field
        greeting_phrase: str = Field(
            default="hello", description="The greeting phrase to use."
        )

    @dg.asset
    def greeting(config: MyAssetConfig) -> str:
        if config.person_name:
            return f"{config.greeting_phrase} {config.person_name}"
        else:
            return config.greeting_phrase

    asset_result = dg.materialize(
        [greeting],
        run_config=dg.RunConfig({"greeting": MyAssetConfig()}),
    )

    # end_optional_config


def execute_with_bad_config() -> None:
    import dagster as dg

    class MyOpConfig(dg.Config):
        person_name: str

    @dg.op
    def print_greeting(config: MyOpConfig):
        print(f"hello {config.person_name}")  # noqa: T201

    class MyAssetConfig(dg.Config):
        person_name: str

    @dg.asset
    def greeting(config: MyAssetConfig) -> str:
        return f"hello {config.person_name}"

    # start_execute_with_bad_config

    @dg.job
    def greeting_job():
        print_greeting()

    op_result = greeting_job.execute_in_process(
        run_config=dg.RunConfig(
            {"print_greeting": MyOpConfig(nonexistent_config_value=1)}  # type: ignore
        ),
    )

    asset_result = dg.materialize(
        [greeting],
        run_config=dg.RunConfig(
            {"greeting": MyAssetConfig(nonexistent_config_value=1)}
        ),  # type: ignore
    )

    # end_execute_with_bad_config


def enum_schema_config() -> None:
    # start_enum_schema_config

    import dagster as dg
    from enum import Enum

    class UserPermissions(Enum):
        GUEST = "guest"
        MEMBER = "member"
        ADMIN = "admin"

    class ProcessUsersConfig(dg.Config):
        users_list: dict[str, UserPermissions]

    @dg.op
    def process_users(config: ProcessUsersConfig):
        for user, permission in config.users_list.items():
            if permission == UserPermissions.ADMIN:
                print(f"{user} is an admin")  # noqa: T201

    @dg.job
    def process_users_job():
        process_users()

    op_result = process_users_job.execute_in_process(
        run_config=dg.RunConfig(
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

    import dagster as dg
    from pydantic import validator

    class UserConfig(dg.Config):
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

    @dg.op
    def greet_user(config: UserConfig) -> None:
        print(f"Hello {config.name}!")  # noqa: T201
        executed["greet_user"] = True

    @dg.job
    def greet_user_job() -> None:
        greet_user()

    # Input is valid, so this will work
    op_result = greet_user_job.execute_in_process(
        run_config=dg.RunConfig(
            {"greet_user": UserConfig(name="Alice Smith", username="alice123")}
        ),
    )

    # Name has no space, so this will fail
    op_result = greet_user_job.execute_in_process(
        run_config=dg.RunConfig(
            {"greet_user": UserConfig(name="John", username="johndoe44")}
        ),
    )

    # end_validated_schema_config


def required_config() -> None:
    # start_required_config
    from typing import Optional
    from collections.abc import Callable
    import dagster as dg
    from pydantic import Field

    class MyAssetConfig(dg.Config):
        # ellipsis indicates that even though the type is Optional,
        # an input is required
        person_first_name: Optional[str] = ...

        # ellipsis can also be used with pydantic.Field to attach metadata
        person_last_name: Optional[Callable] = Field(
            default=..., description="The last name of the person to greet"
        )

    @dg.asset
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
