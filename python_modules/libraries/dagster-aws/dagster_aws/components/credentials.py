from typing import Any, cast

import dagster as dg
from dagster._annotations import preview, public
from pydantic import BaseModel, create_model

from dagster_aws.components.utils import copy_fields_from_model
from dagster_aws.utils import ResourceWithBoto3Configuration


def _copy_fields_to_model(
    copy_from: type[BaseModel], copy_to: type[BaseModel], new_model_cls_name: str
) -> type[BaseModel]:
    field_definitions = copy_fields_from_model(copy_from)
    return cast(
        "type[BaseModel]",
        create_model(
            new_model_cls_name,
            __base__=copy_to,
            **cast("dict[str, Any]", field_definitions),
        ),
    )


class Boto3CredentialsComponentBase(dg.Component, dg.Resolvable, dg.Model):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()


Boto3CredentialsComponent = public(preview)(
    _copy_fields_to_model(
        copy_from=ResourceWithBoto3Configuration,
        copy_to=Boto3CredentialsComponentBase,
        new_model_cls_name="Boto3CredentialsComponent",
    )
)
