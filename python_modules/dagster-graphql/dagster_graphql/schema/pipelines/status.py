# pylint: disable=missing-graphene-docstring
import graphene


class GrapheneRunStatus(graphene.Enum):
    QUEUED = "QUEUED"
    NOT_STARTED = "NOT_STARTED"
    MANAGED = "MANAGED"
    STARTING = "STARTING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"

    class Meta:
        name = "RunStatus"
