from typing import Any

from pydantic import BaseModel

from dagster_rest_resources.schemas.util import DgApiList


class DgApiCodeSource(BaseModel):
    python_file: str | None = None
    module_name: str | None = None
    package_name: str | None = None
    autoload_defs_module_name: str | None = None


class DgApiGitMetadata(BaseModel):
    commit_hash: str | None = None
    url: str | None = None


class DgApiCodeLocationDocument(BaseModel):
    location_name: str
    image: str | None = None
    code_source: DgApiCodeSource | None = None
    working_directory: str | None = None
    executable_path: str | None = None
    attribute: str | None = None
    git: DgApiGitMetadata | None = None

    def to_document_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class DgApiAddCodeLocationResult(BaseModel):
    location_name: str


class DgApiDeleteCodeLocationResult(BaseModel):
    location_name: str


class DgApiCodeLocation(BaseModel):
    location_name: str
    image: str | None = None
    status: str | None = None
    code_source: DgApiCodeSource | None = None


class DgApiCodeLocationList(DgApiList["DgApiCodeLocation"]):
    pass
