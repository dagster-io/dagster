from pydantic import BaseModel  # pylint: disable=E0611

from .dagit import Dagit
from .postgresql import PostgreSQL


class HelmValues(BaseModel):
    """
    Schema for Helm values.
    """

    dagit: Dagit
    postgresql: PostgreSQL
