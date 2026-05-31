from app.core.exceptions import ForbiddenError
from app.utils.enums import RoleEnum
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskUpdate


class TaskPolicy:
    def __init__(self, user: User, task: Task) -> None:
        self.user = user
        self.task = task
        self.role = user.role.name

    def can_read(self) -> None:
        if self.role == RoleEnum.ADMIN:
            return
        if self.role == RoleEnum.MANAGER and self._owns_or_assigned():
            return
        if self.role == RoleEnum.USER and self._is_assignee():
            return
        raise ForbiddenError("You do not have access to this task")

    def can_update(self, payload: TaskUpdate) -> None:
        if self.role == RoleEnum.ADMIN:
            return

        if self.role == RoleEnum.MANAGER:
            if not self._owns_or_assigned():
                raise ForbiddenError(
                    "Managers can only update tasks they created or are assigned to"
                )
            return

        if not self._is_assignee():
            raise ForbiddenError("You can only update tasks assigned to you")

        non_status_fields = {
            k for k in payload.model_dump(exclude_none=True) if k != "status"
        }
        if non_status_fields:
            raise ForbiddenError("Users can only update task status")

    def can_assign(self) -> None:
        if self.role == RoleEnum.ADMIN:
            return
        if self.role == RoleEnum.MANAGER and self.task.created_by == self.user.id:
            return
        raise ForbiddenError("Managers can only assign tasks they created")

    def _owns_or_assigned(self) -> bool:
        return (
            self.task.created_by == self.user.id
            or self.task.assigned_to == self.user.id
        )

    def _is_assignee(self) -> bool:
        return self.task.assigned_to == self.user.id
