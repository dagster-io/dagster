from typing import Dict

from dagster._record import record
from looker_sdk.sdk.api40.models import LookmlModelExplore


@record
class LookerInstanceData:
    """A record representing all content in a Looker instance.

    Provided as context for the translator so that it can resolve dependencies between structures.
    """

    explores_by_id: Dict[str, LookmlModelExplore]
