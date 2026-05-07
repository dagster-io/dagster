from pydantic import BaseModel

from dagster_rest_resources.schemas.util import DgApiList


class DgApiStepComputeLog(BaseModel):
    file_key: str
    step_keys: list[str]
    stdout: str | None = None
    stderr: str | None = None
    cursor: str | None = None


class DgApiStepComputeLogLink(BaseModel):
    file_key: str
    step_keys: list[str]
    stdout_download_url: str | None = None
    stderr_download_url: str | None = None


class DgApiComputeLogList(DgApiList[DgApiStepComputeLog]):
    run_id: str


class DgApiComputeLogLinkList(DgApiList[DgApiStepComputeLogLink]):
    run_id: str
