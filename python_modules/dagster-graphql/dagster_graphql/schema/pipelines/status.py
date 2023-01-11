import dagster._check as check
import graphene


class GrapheneRunStatus(graphene.Enum):
    """The status of run execution."""

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

    @property
    def description(self: "GrapheneRunStatus") -> str:
        if self == GrapheneRunStatus.QUEUED:
            return "Runs waiting to be launched by the Dagster Daemon."
        elif self == GrapheneRunStatus.NOT_STARTED:
            return "Runs that have been created, but not yet submitted for launch."
        elif self == GrapheneRunStatus.MANAGED:
            return "Runs that are managed outside of the Dagster control plane."
        elif self == GrapheneRunStatus.STARTING:
            return "Runs that have been launched, but execution has not yet started."
        elif self == GrapheneRunStatus.STARTED:
            return "Runs that have been launched and execution has started."
        elif self == GrapheneRunStatus.SUCCESS:
            return "Runs that have successfully completed."
        elif self == GrapheneRunStatus.FAILURE:
            return "Runs that have failed to complete."
        elif self == GrapheneRunStatus.CANCELING:
            return "Runs that are in-progress and pending to be canceled."
        elif self == GrapheneRunStatus.CANCELED:
            return "Runs that have been canceled before completion."
        else:
            check.assert_never(self)
