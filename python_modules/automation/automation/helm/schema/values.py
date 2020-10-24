from pydantic import BaseModel  # pylint: disable=E0611

from .dagit import Dagit


class HelmValues(BaseModel):
    """
    Schema for Helm values.
    """

    dagit: Dagit
