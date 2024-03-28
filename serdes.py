from dagster._serdes import serialize_value, whitelist_for_serdes
from pydantic import BaseModel


class Foo(BaseModel):
    num: int

@whitelist_for_serdes
class Bar(BaseModel):
    num: int


print(serialize_value(Foo(num=1)))
print(serialize_value(Bar(num=1)))
