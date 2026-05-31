from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    full_name: str | None = None
    email: EmailStr
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class PaginatedUsersOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserOut]
