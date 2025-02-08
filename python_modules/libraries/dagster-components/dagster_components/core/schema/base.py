from pydantic import BaseModel, ConfigDict


class ComponentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
