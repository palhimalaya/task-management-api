from datetime import datetime

from pydantic import BaseModel

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None
    assigned_to: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None


class TaskAssign(BaseModel):
    assigned_to: int


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by: int | None
    assigned_to: int | None

    model_config = {"from_attributes": True}


class PaginatedTasksOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TaskOut]
