from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def list_all_users(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[User], int]:
    query = select(User)

    total = await db.scalar(select(func.count()).select_from(User)) or 0

    offset = (page - 1) * page_size

    result = await db.execute(query.order_by(User.id).offset(offset).limit(page_size))

    return list(result.scalars().all()), total
