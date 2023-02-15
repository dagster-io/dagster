# isort: skip_file
# pylint: disable=unused-argument,reimported,unnecessary-ellipsis
from dagster import ResourceDefinition, graph, job, Definitions, resource, op, asset
import requests
from requests import Response
from typing import Generic, List, TypeVar
from dagster._config.structured_config import Config, ConfigurableResource


# start_basic_op_config


class MyOpConfig(Config):
    person_name: str


@op
def print_greeting(config: MyOpConfig):
    print(f"hello {config.person_name}")


# end_basic_op_config

# start_basic_asset_config


class MyAssetConfig(Config):
    person_name: str


@asset
def greeting(config: MyAssetConfig) -> str:
    return f"hello {config.person_name}"


# end_basic_asset_config


class Engine:
    def execute(self, query: str):
        ...


def get_engine(connection_url: str) -> Engine:
    return Engine()


# start_basic_resource_config


class MyDatabaseResource(ConfigurableResource):
    connection_url: str

    def query(self, query: str) -> Response:
        return get_engine(self.connection_url).execute(query)


# end_basic_resource_config

from typing import NamedTuple, Dict, Any, Mapping, Optional
from dagster import materialize


class RunConfig(Dict[str, Any]):
    def __init__(
        self,
        ops: Optional[Dict[str, Any]] = None,
        assets: Optional[Dict[str, Any]] = None,
        resources: Optional[Dict[str, Any]] = None,
    ):
        super().__init__({**(ops or {}), **(assets or {}), **(resources or {})})


# start_execute_with_config


@job
def greeting_job():
    print_greeting()


job_result = greeting_job.execute_in_process(
    run_config=RunConfig(ops={"print_greeting": MyOpConfig(person_name="Alice")})
)

asset_result = materialize(
    [greeting],
    run_config=RunConfig(assets={"greeting": MyAssetConfig(person_name="Alice")}),
)

# end_execute_with_config


# start_basic_data_structures_config


class MyDataStructuresConfig(Config):
    user_names: List[str]
    user_scores: Dict[str, int]


@asset
def scoreboard(config: MyDataStructuresConfig):
    ...


result = materialize(
    [scoreboard],
    run_config=RunConfig(
        assets={
            "scoreboard": MyDataStructuresConfig(
                user_names=["Alice", "Bob"],
                user_scores={"Alice": 10, "Bob": 20},
            )
        }
    ),
)


# end_basic_data_structures_config


# start_nested_schema_config


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
        assets={
            "average_age": MyNestedConfig(
                user_data={
                    "Alice": UserData(age=10, email="alice@gmail.com", profile_picture_url=...),
                    "Bob": UserData(age=20, email="bob@gmail.com", profile_picture_url=...),
                }
            )
        }
    ),
)


# end_nested_schema_config

from typing import Union
from pydantic import Field
from typing_extensions import Literal

# start_union_schema_config


class Cat(Config):
    pet_type: Literal["cat"]
    meows: int


class Dog(Config):
    pet_type: Literal["dog"]
    barks: float


class ConfigWithUnion(Config):
    pet: Union[Cat, Dog] = Field(..., discriminator="pet_type")


@asset
def pet_stats(config: ConfigWithUnion):
    if isinstance(config.pet, Cat):
        return f"Cat meows {config.pet.meows} times"
    else:
        return f"Dog barks {config.pet.barks} times"


result = materialize(
    [pet_stats],
    run_config=RunConfig(
        assets={
            "pet_stats": ConfigWithUnion(
                pet=Cat(pet_type="cat", meows=10),
            )
        }
    ),
)
# end_union_schema_config


#  start_metadata_config


class MyMetadataConfig(Config):
    person_name: str = Field(..., description="The name of the person to greet")
    age: int = Field(..., gt=0, lt=100, description="The age of the person to greet")


# errors!
MyMetadataConfig(person_name="Alice", age=200)

# end_metadata_config
