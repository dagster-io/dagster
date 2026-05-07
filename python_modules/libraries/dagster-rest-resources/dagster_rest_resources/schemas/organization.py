from typing import Any

from pydantic import BaseModel


class DgApiOrganizationSettings(BaseModel):
    settings: dict[str, Any]
