from app.models.user import User
from app.schemas.task import TaskAssign, TaskCreate, TaskOut, TaskUpdate
from app.models.task import Task
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from sqlalchemy import or_, select, func
from app.utils.enums import RoleEnum, TaskStatus
from app.policies.task_policy import TaskPolicy

_BLOCKED_BACKWARD = {TaskStatus.PENDING, TaskStatus.IN_PROGRESS}


async def create_task(
    payload: TaskCreate,
    current_user: User,
    db: AsyncSession,
) -> TaskOut:

    if payload.assigned_to is not None:
        await _validate_assignee_exists(payload.assigned_to, db)

    task = Task(
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        assigned_to=payload.assigned_to,
        created_by=current_user.id,
    )
    db.add(task)
    await db.flush()
    return task


async def list_tasks(
    current_user: User,
    db: AsyncSession,
    *,
    status: TaskStatus | None = None,
    assigned_to: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Task], int]:
    role = current_user.role.name
    query = select(Task)

    if role == RoleEnum.USER:
        query = query.where(Task.assigned_to == current_user.id)
    elif role == RoleEnum.MANAGER:
        query = query.where(
            or_(Task.created_by == current_user.id, Task.assigned_to == current_user.id)
        )

    if status is not None:
        query = query.where(Task.status == status)
    if assigned_to is not None:
        query = query.where(Task.assigned_to == assigned_to)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    offset = (page - 1) * page_size
    query = query.order_by(Task.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)

    return list(result.scalars().all()), total


async def get_task(task_id: int, current_user: User, db: AsyncSession) -> Task:
    task = await _get_or_404(task_id, db)
    TaskPolicy(current_user, task).can_read()
    return task


async def update_task(
    task_id: int, payload: TaskUpdate, current_user: User, db: AsyncSession
) -> Task:
    task = await _get_or_404(task_id, db)
    TaskPolicy(current_user, task).can_update(payload)

    if payload.status is not None:
        _validate_status_transition(task.status, payload.status)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(task, field, value)

    await db.flush()
    return task


async def delete_task(task_id: int, current_user: User, db: AsyncSession) -> None:
    task = await _get_or_404(task_id, db)
    await db.delete(task)
    await db.flush()


async def assign_task(
    task_id: int, payload: TaskAssign, current_user: User, db: AsyncSession
) -> Task:
    task = await _get_or_404(task_id, db)
    TaskPolicy(current_user, task).can_assign()

    await _validate_assignee_exists(payload.assigned_to, db)
    task.assigned_to = payload.assigned_to
    await db.flush()
    await db.refresh(task)
    return task


async def _get_or_404(task_id: int, db: AsyncSession) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise NotFoundError(f"Task {task_id} not found")
    return task


def _validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    if current == TaskStatus.COMPLETED and new in _BLOCKED_BACKWARD:
        raise BadRequestError(
            f"Cannot transition task from COMPLETED to {new.value}. "
            "Completed tasks cannot be moved backwards."
        )


async def _validate_assignee_exists(user_id: int, db: AsyncSession) -> None:
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
