from pydantic import BaseModel

class TenantCreate(BaseModel):
    name: str

class TenantRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True