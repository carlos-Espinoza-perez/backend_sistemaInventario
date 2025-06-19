from pydantic import BaseModel
from datetime import datetime

class ItemBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    category_id: int | None = None

class ItemCreate(ItemBase):
    pass

class ItemOut(ItemBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True