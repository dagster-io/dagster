from pydantic import BaseModel

from dagster_components.core.component import Component
from dagster_components.core.resolution_engine.resolver import Resolver, resolver
from dagster_components.core.schema.base import ComponentSchema


class LevelTwoSchema(ComponentSchema):
    level_two: str


class LevelOneSchema(ComponentSchema):
    sub_schema: LevelTwoSchema
    level_one: str


class LevelZeroSchema(ComponentSchema):
    sub_schema: LevelOneSchema
    level_zero: str


class BusinessObjectTwo(BaseModel):
    level_two: str


class BusinessObjectOne(BaseModel):
    level_one: str
    sub_schema: BusinessObjectTwo


class BusinessObjectZero(BaseModel):
    level_zero: str
    sub_schema: BusinessObjectOne


@resolver(fromtype=LevelZeroSchema, totype=BusinessObjectZero)
class ResolvedLevelZero(Resolver):
    def resolve_level_zero(self, context) -> str:
        return self.schema.level_zero + "_computed"


@resolver(fromtype=LevelOneSchema, totype=BusinessObjectOne)
class ResolvedLevelOne(Resolver):
    def resolve_level_one(self, context) -> str:
        return self.schema.level_one + "_computed"


@resolver(fromtype=LevelTwoSchema, totype=BusinessObjectTwo)
class ResolvedLevelTwo(Resolver):
    def resolve_level_two(self, context) -> str:
        return self.schema.level_two + "_computed"


class NestedResolvedComponent(Component):
    def __init__(self, level_zero: str, sub_schema: BusinessObjectOne):
        self.level_zero = level_zero
        self.sub_schema = sub_schema

    def get_schema(self):
        return LevelZeroSchema

    def build_defs(self, context): ...
