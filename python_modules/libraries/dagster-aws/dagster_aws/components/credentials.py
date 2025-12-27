from typing import Any, Optional, cast

import dagster as dg
from dagster._annotations import preview, public
from pydantic import BaseModel, create_model

from dagster_aws.components.utils import copy_fields_from_model
from dagster_aws.utils import ResourceWithBoto3Configuration


def _copy_fields_to_model(
    copy_from: type[BaseModel], copy_to: type[BaseModel], new_model_cls_name: str
) -> type[BaseModel]:
    field_definitions = copy_fields_from_model(copy_from)
    return create_model(
        new_model_cls_name,
        __base__=copy_to,
        **cast("dict[str, Any]", field_definitions),
    )


class Boto3CredentialsComponentBase(dg.Component, dg.Resolvable, dg.Model):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()


_Boto3Dynamic = _copy_fields_to_model(
    ResourceWithBoto3Configuration, Boto3CredentialsComponentBase, "Boto3CredentialsComponent"
)


@public
@preview
class Boto3CredentialsComponent(cast("Any", _Boto3Dynamic)):
    pass


class S3CredentialsComponentBase(Boto3CredentialsComponent):
    use_unsigned_session: Optional[bool] = None


_S3Dynamic = _copy_fields_to_model(
    ResourceWithBoto3Configuration, S3CredentialsComponentBase, "S3CredentialsComponent"
)


@public
@preview
class S3CredentialsComponent(cast("Any", _S3Dynamic)):
    pass
