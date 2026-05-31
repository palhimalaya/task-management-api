from unittest.mock import MagicMock

import pytest

from app.services.user_service import list_all_users


@pytest.mark.asyncio
async def test_list_all_users_returns_users(mock_db):
    user1 = MagicMock()
    user2 = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        user1,
        user2,
    ]

    mock_db.execute.return_value = result

    users = await list_all_users(mock_db)

    assert users == [user1, user2]

    mock_db.execute.assert_awaited_once()
