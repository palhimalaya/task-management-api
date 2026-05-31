from unittest.mock import MagicMock

import pytest

from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import login_user, register_user


def _mock_user(
    user_id: int = 10,
    is_active: bool = True,
) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.is_active = is_active
    user.password_hash = hash_password("correctpass")
    return user


def _mock_role(role_id: int = 1) -> MagicMock:
    role = MagicMock()
    role.id = role_id
    return role


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_success(self, mock_db):
        mock_db.scalar.side_effect = [
            None,
            _mock_role(),
        ]

        token = await register_user(
            RegisterRequest(
                full_name="John Doe",
                email="john@example.com",
                password="password123",
            ),
            mock_db,
        )

        assert isinstance(token, str)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_duplicate_email(self, mock_db):
        mock_db.scalar.return_value = MagicMock()

        with pytest.raises(ConflictError):
            await register_user(
                RegisterRequest(
                    full_name="John Doe",
                    email="john@example.com",
                    password="password123",
                ),
                mock_db,
            )

        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_default_role(self, mock_db):
        mock_db.scalar.return_value = None

        with pytest.raises(RuntimeError):
            await register_user(
                RegisterRequest(
                    full_name="John Doe",
                    email="john@example.com",
                    password="password123",
                ),
                mock_db,
            )


class TestLoginUser:
    @pytest.mark.asyncio
    async def test_success(self, mock_db):
        user = _mock_user()
        user.password_hash = hash_password("password123")

        mock_db.scalar.return_value = user

        token = await login_user(
            LoginRequest(
                email="john@example.com",
                password="password123",
            ),
            mock_db,
        )

        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_unknown_email(self, mock_db):
        mock_db.scalar.return_value = None

        with pytest.raises(ConflictError):
            await login_user(
                LoginRequest(
                    email="john@example.com",
                    password="password123",
                ),
                mock_db,
            )

    @pytest.mark.asyncio
    async def test_wrong_password(self, mock_db):
        user = _mock_user()
        user.password_hash = hash_password("correct-password")

        mock_db.scalar.return_value = user

        with pytest.raises(ConflictError):
            await login_user(
                LoginRequest(
                    email="john@example.com",
                    password="wrong-password",
                ),
                mock_db,
            )
