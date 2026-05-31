from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.utils.enums import RoleEnum, TaskStatus
from app.schemas.task import TaskAssign, TaskCreate, TaskUpdate
from app.services.task_service import (
    _validate_status_transition,
    assign_task,
    create_task,
    delete_task,
    get_task,
    update_task,
)


def _mock_user(
    user_id: int = 1,
    role: RoleEnum = RoleEnum.ADMIN,
) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.role.name = role
    return user


def _mock_task(
    task_id: int = 1,
    status: TaskStatus = TaskStatus.PENDING,
) -> MagicMock:
    task = MagicMock()
    task.id = task_id
    task.status = status
    task.created_by = 1
    task.assigned_to = None
    return task


class TestValidateStatusTransition:
    def test_completed_to_pending_raises(self):
        with pytest.raises(BadRequestError):
            _validate_status_transition(
                TaskStatus.COMPLETED,
                TaskStatus.PENDING,
            )

    def test_completed_to_in_progress_raises(self):
        with pytest.raises(BadRequestError):
            _validate_status_transition(
                TaskStatus.COMPLETED,
                TaskStatus.IN_PROGRESS,
            )

    def test_pending_to_in_progress_is_allowed(self):
        _validate_status_transition(
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
        )

    def test_pending_to_completed_is_allowed(self):
        _validate_status_transition(
            TaskStatus.PENDING,
            TaskStatus.COMPLETED,
        )

    def test_in_progress_to_completed_is_allowed(self):
        _validate_status_transition(
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
        )

    def test_in_progress_to_pending_is_allowed(self):
        _validate_status_transition(
            TaskStatus.IN_PROGRESS,
            TaskStatus.PENDING,
        )

    def test_same_status_does_not_raise(self):
        _validate_status_transition(
            TaskStatus.COMPLETED,
            TaskStatus.COMPLETED,
        )
        _validate_status_transition(
            TaskStatus.PENDING,
            TaskStatus.PENDING,
        )


class TestCreateTask:
    @pytest.mark.asyncio
    async def test_creates_task_with_correct_fields(self, mock_db):
        db = mock_db
        user = _mock_user(user_id=5)

        task = await create_task(
            TaskCreate(title="My Task"),
            user,
            db,
        )

        assert task.title == "My Task"
        assert task.created_by == 5

        db.add.assert_called_once_with(task)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_validates_assignee_when_provided(self, mock_db):
        db = mock_db
        db.get.return_value = _mock_user(user_id=99)

        task = await create_task(
            TaskCreate(
                title="Assigned Task",
                assigned_to=99,
            ),
            _mock_user(),
            db,
        )

        db.get.assert_awaited_once()
        assert task.assigned_to == 99

    @pytest.mark.asyncio
    async def test_raises_not_found_when_assignee_missing(self, mock_db):
        db = mock_db
        db.get.return_value = None

        with pytest.raises(NotFoundError):
            await create_task(
                TaskCreate(
                    title="Bad Task",
                    assigned_to=999,
                ),
                _mock_user(),
                db,
            )

    @pytest.mark.asyncio
    async def test_no_db_lookup_when_no_assignee(self, mock_db):
        db = mock_db

        await create_task(
            TaskCreate(title="Unassigned"),
            _mock_user(),
            db,
        )

        db.get.assert_not_awaited()


class TestGetTask:
    @pytest.mark.asyncio
    async def test_returns_task_when_found_and_allowed(self, mock_db):
        db = mock_db

        task = _mock_task()

        db.get.return_value = task

        with patch("app.services.task_service.TaskPolicy") as policy:
            policy.return_value.can_read.return_value = None

            result = await get_task(
                1,
                _mock_user(),
                db,
            )

        assert result is task

    @pytest.mark.asyncio
    async def test_raises_not_found_when_task_missing(self, mock_db):
        db = mock_db

        db.get.return_value = None

        with pytest.raises(NotFoundError):
            await get_task(
                999,
                _mock_user(),
                db,
            )


class TestUpdateTask:
    @pytest.mark.asyncio
    async def test_updates_fields_on_task(self, mock_db):
        db = mock_db

        task = _mock_task()

        db.get.return_value = task

        with patch("app.services.task_service.TaskPolicy") as policy:
            policy.return_value.can_update.return_value = None

            result = await update_task(
                1,
                TaskUpdate(title="New Title"),
                _mock_user(),
                db,
            )

        assert result.title == "New Title"

        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_task_missing(self, mock_db):
        db = mock_db

        db.get.return_value = None

        with pytest.raises(NotFoundError):
            await update_task(
                999,
                TaskUpdate(title="x"),
                _mock_user(),
                db,
            )

    @pytest.mark.asyncio
    async def test_rejects_blocked_status_transition(self, mock_db):
        db = mock_db

        task = _mock_task(
            status=TaskStatus.COMPLETED,
        )

        db.get.return_value = task

        with patch("app.services.task_service.TaskPolicy") as policy:
            policy.return_value.can_update.return_value = None

            with pytest.raises(BadRequestError):
                await update_task(
                    1,
                    TaskUpdate(
                        status=TaskStatus.PENDING,
                    ),
                    _mock_user(),
                    db,
                )


class TestDeleteTask:
    @pytest.mark.asyncio
    async def test_deletes_task_from_session(self, mock_db):
        db = mock_db

        task = _mock_task()

        db.get.return_value = task

        await delete_task(
            1,
            _mock_user(),
            db,
        )

        db.delete.assert_awaited_once_with(task)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_task_missing(self, mock_db):
        db = mock_db

        db.get.return_value = None

        with pytest.raises(NotFoundError):
            await delete_task(
                999,
                _mock_user(),
                db,
            )


class TestAssignTask:
    @pytest.mark.asyncio
    async def test_sets_assigned_to_on_task(self, mock_db):
        db = mock_db

        task = _mock_task()

        db.get.side_effect = [
            task,
            _mock_user(user_id=7),
        ]

        with patch("app.services.task_service.TaskPolicy") as policy:
            policy.return_value.can_assign.return_value = None

            result = await assign_task(
                1,
                TaskAssign(assigned_to=7),
                _mock_user(),
                db,
            )

        assert result.assigned_to == 7

        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_task_missing(self, mock_db):
        db = mock_db

        db.get.return_value = None

        with pytest.raises(NotFoundError):
            await assign_task(
                999,
                TaskAssign(assigned_to=1),
                _mock_user(),
                db,
            )

    @pytest.mark.asyncio
    async def test_raises_not_found_when_assignee_missing(self, mock_db):
        db = mock_db

        task = _mock_task()

        db.get.side_effect = [
            task,
            None,
        ]

        with patch("app.services.task_service.TaskPolicy") as policy:
            policy.return_value.can_assign.return_value = None

            with pytest.raises(NotFoundError):
                await assign_task(
                    1,
                    TaskAssign(assigned_to=999),
                    _mock_user(),
                    db,
                )
