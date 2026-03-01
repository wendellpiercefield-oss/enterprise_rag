from pydantic import BaseModel


class CollectionMemberCreate(BaseModel):
    user_id: int
    role: str = "member"