from pydantic import BaseModel, ConfigDict


class CollectionCreate(BaseModel):
    name: str


class CollectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tenant_id: int
    created_by: int