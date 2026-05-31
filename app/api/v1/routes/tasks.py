from fastapi import APIRouter, Query

from app.api.v1.deps.permissions import AdminDep, AdminOrManagerDep
from app.api.v1.deps.auth import CurrentUserDep
from app.db.session import DBSessionDep
from app.utils.enums import TaskStatus
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.task import (
    PaginatedTasksOut,
    TaskAssign,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)
from app.services import task_service
from app.utils.response import created, success

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)


@router.post(
    "",
    summary="Create a task",
    description="Create a new task. **ADMIN and MANAGER only.**",
    status_code=201,
    response_model=ApiResponse[TaskOut],
    responses={
        404: {"model": ErrorResponse, "description": "Assigned user not found"},
    },
)
async def create_task(
    payload: TaskCreate,
    db: DBSessionDep,
    current_user: AdminOrManagerDep,
) -> ApiResponse[TaskOut]:
    task = await task_service.create_task(payload, current_user, db)
    return created(
        data=TaskOut.model_validate(task),
        message="Task created successfully",
    )


@router.get(
    "",
    summary="List tasks",
    description=(
        "Returns tasks visible to the current user. "
        "ADMIN sees all, MANAGER sees own/assigned, USER sees assigned only. "
        "Supports filtering by status and assigned_to, plus pagination."
    ),
    response_model=ApiResponse[PaginatedTasksOut],
)
async def list_tasks(
    db: DBSessionDep,
    current_user: CurrentUserDep,
    status: TaskStatus | None = Query(None, description="Filter by task status"),
    assigned_to: int | None = Query(None, description="Filter by assigned user ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
) -> ApiResponse[PaginatedTasksOut]:
    tasks, total = await task_service.list_tasks(
        current_user,
        db,
        status=status,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size,
    )
    paginated = PaginatedTasksOut(
        total=total,
        page=page,
        page_size=page_size,
        items=[TaskOut.model_validate(t) for t in tasks],
    )
    return success(data=paginated, message=f"{total} task(s) found")


@router.get(
    "/{task_id}",
    summary="Get a single task",
    description=(
        "Fetch a task by ID."
        "ADMIN can access all, MANAGER can access own/assigned, USER can access assigned only."
    ),
    response_model=ApiResponse[TaskOut],
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
async def get_task(
    task_id: int,
    db: DBSessionDep,
    current_user: CurrentUserDep,
) -> ApiResponse[TaskOut]:
    task = await task_service.get_task(task_id, current_user, db)
    return success(data=TaskOut.model_validate(task))


@router.patch(
    "/{task_id}",
    summary="Update a task",
    description=(
        "Partially update a task. "
        "ADMIN can update any task. "
        "MANAGER can update tasks they created. "
        "USER can update only the status of tasks assigned to them."
    ),
    response_model=ApiResponse[TaskOut],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid status transition"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: DBSessionDep,
    current_user: CurrentUserDep,
) -> ApiResponse[TaskOut]:
    task = await task_service.update_task(task_id, payload, current_user, db)
    await db.refresh(task)
    return success(
        data=TaskOut.model_validate(task),
        message="Task updated",
    )

@router.delete(
    "/{task_id}",
    summary="Delete a task",
    description="Permanently delete a task. **ADMIN only.**",
    status_code=200,
    response_model=ApiResponse[None],
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
async def delete_task(
    task_id: int,
    db: DBSessionDep,
    current_user: AdminDep,
) -> ApiResponse[None]:
    await task_service.delete_task(task_id, current_user, db)
    return success(message="Task deleted successfully")


@router.patch(
    "/{task_id}/assign",
    summary="Assign a task",
    description="Assign a task to a user. **ADMIN and MANAGER only.**",
    response_model=ApiResponse[TaskOut],
    responses={
        404: {"model": ErrorResponse, "description": "Task or user not found"},
    },
)
async def assign_task(
    task_id: int,
    payload: TaskAssign,
    db: DBSessionDep,
    current_user: AdminOrManagerDep,
) -> ApiResponse[TaskOut]:
    task = await task_service.assign_task(task_id, payload, current_user, db)
    return success(
        data=TaskOut.model_validate(task),
        message=f"Task assigned to user {payload.assigned_to}",
    )
