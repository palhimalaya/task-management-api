from unittest.mock import MagicMock

import pytest

from app.services.user_service import list_all_users


class TestListAllUsers:
    @pytest.mark.asyncio
    async def test_returns_paginated_users(self, mock_db):
        user1 = MagicMock()
        user2 = MagicMock()

        result = MagicMock()
        result.scalars.return_value.all.return_value = [
            user1,
            user2,
        ]

        mock_db.scalar.return_value = 2
        mock_db.execute.return_value = result

        users, total = await list_all_users(
            mock_db,
            page=1,
            page_size=20,
        )

        assert users == [user1, user2]
        assert total == 2

        mock_db.scalar.assert_awaited_once()
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_empty_result(self, mock_db):
        result = MagicMock()
        result.scalars.return_value.all.return_value = []

        mock_db.scalar.return_value = 0
        mock_db.execute.return_value = result

        users, total = await list_all_users(
            mock_db,
            page=1,
            page_size=20,
        )

        assert users == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_uses_pagination_parameters(self, mock_db):
        result = MagicMock()
        result.scalars.return_value.all.return_value = []

        mock_db.scalar.return_value = 100
        mock_db.execute.return_value = result

        users, total = await list_all_users(
            mock_db,
            page=3,
            page_size=10,
        )

        assert users == []
        assert total == 100

        mock_db.execute.assert_awaited_once()
