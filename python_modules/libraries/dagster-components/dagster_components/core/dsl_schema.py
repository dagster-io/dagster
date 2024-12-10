from typing import Dict, Optional

from pydantic import BaseModel


class OpSpecBaseModel(BaseModel):
    name: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
