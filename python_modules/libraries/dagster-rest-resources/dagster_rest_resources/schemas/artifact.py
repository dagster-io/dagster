from pydantic import BaseModel


class DgApiArtifactUploadResult(BaseModel):
    key: str
    deployment: str | None = None


class DgApiArtifactDownloadResult(BaseModel):
    key: str
    deployment: str | None = None
    path: str
