import dagster as dg


class MyOpConfig(dg.Config):
    person_name: str


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(resources={"config": MyOpConfig(person_name="")})
