import dagster as dg


class MyAssetConfig(dg.Config):
    person_name: str


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(resources={"config": MyAssetConfig(person_name="")})
