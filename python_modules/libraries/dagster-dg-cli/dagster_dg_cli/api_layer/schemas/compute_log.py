"""Compute log schema definitions."""

from pydantic import BaseModel


class DgApiStepComputeLog(BaseModel):
    """Per-step compute log content."""

    file_key: str
    step_keys: list[str]
    stdout: str | None = None
    stderr: str | None = None
    cursor: str | None = None

    class Config:
        from_attributes = True


class DgApiStepComputeLogLink(BaseModel):
    """Per-step compute log download URLs."""

    file_key: str
    step_keys: list[str]
    stdout_download_url: str | None = None
    stderr_download_url: str | None = None

    class Config:
        from_attributes = True


class DgApiComputeLogList(BaseModel):
    """Compute log content response."""

    run_id: str
    items: list[DgApiStepComputeLog]
    total: int

    class Config:
        from_attributes = True


class DgApiComputeLogLinkList(BaseModel):
    """Compute log links response."""

    run_id: str
    items: list[DgApiStepComputeLogLink]
    total: int

    class Config:
        from_attributes = True
