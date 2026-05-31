from unittest.mock import MagicMock

import pytest

from app.core.exceptions import ForbiddenError
from app.policies.task_policy import TaskPolicy
from app.schemas.task import TaskUpdate
from app.utils.enums import RoleEnum


def _user(user_id: int, role: RoleEnum):
    user = MagicMock()
    user.id = user_id
    user.role.name = role
    return user


def _task(
    created_by: int = 1,
    assigned_to: int | None = None,
):
    task = MagicMock()
    task.created_by = created_by
    task.assigned_to = assigned_to
    return task


class TestCanRead:
    def test_admin_can_read_any_task(self):
        TaskPolicy(
            _user(1, RoleEnum.ADMIN),
            _task(created_by=99),
        ).can_read()

    def test_manager_can_read_owned_task(self):
        TaskPolicy(
            _user(1, RoleEnum.MANAGER),
            _task(created_by=1),
        ).can_read()

    def test_user_can_read_assigned_task(self):
        TaskPolicy(
            _user(1, RoleEnum.USER),
            _task(assigned_to=1),
        ).can_read()

    def test_user_cannot_read_other_task(self):
        with pytest.raises(ForbiddenError):
            TaskPolicy(
                _user(1, RoleEnum.USER),
                _task(assigned_to=2),
            ).can_read()


class TestCanUpdate:
    def test_admin_can_update(self):
        TaskPolicy(
            _user(1, RoleEnum.ADMIN),
            _task(),
        ).can_update(TaskUpdate(title="updated"))

    def test_user_can_update_status_only(self):
        TaskPolicy(
            _user(1, RoleEnum.USER),
            _task(assigned_to=1),
        ).can_update(TaskUpdate(status="IN_PROGRESS"))

    def test_user_cannot_update_title(self):
        with pytest.raises(ForbiddenError):
            TaskPolicy(
                _user(1, RoleEnum.USER),
                _task(assigned_to=1),
            ).can_update(TaskUpdate(title="new title"))


class TestCanAssign:
    def test_admin_can_assign(self):
        TaskPolicy(
            _user(1, RoleEnum.ADMIN),
            _task(),
        ).can_assign()

    def test_manager_can_assign_own_task(self):
        TaskPolicy(
            _user(1, RoleEnum.MANAGER),
            _task(created_by=1),
        ).can_assign()

    def test_manager_cannot_assign_other_task(self):
        with pytest.raises(ForbiddenError):
            TaskPolicy(
                _user(1, RoleEnum.MANAGER),
                _task(created_by=2),
            ).can_assign()

    def test_user_cannot_assign(self):
        with pytest.raises(ForbiddenError):
            TaskPolicy(
                _user(1, RoleEnum.USER),
                _task(created_by=1),
            ).can_assign()
