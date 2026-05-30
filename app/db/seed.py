from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.utils.enums import RoleEnum
from app.models.user import User

_DEFAULT_ROLES: list[str] = [RoleEnum.ADMIN, RoleEnum.MANAGER, RoleEnum.USER]


async def seed_roles(session: AsyncSession) -> None:
    for role_name in _DEFAULT_ROLES:
        await session.execute(
            text(
                "INSERT INTO roles (name) VALUES (:name) "
                "ON CONFLICT (name) DO NOTHING"
            ),
            {"name": role_name},
        )
    await session.commit()


async def seed_admin_user(session: AsyncSession) -> None:
    email = settings.ADMIN_EMAIL
    password = settings.ADMIN_PASSWORD

    if not email or not password:
        return

    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        return

    role_row = await session.execute(
        text("SELECT id FROM roles WHERE name = :name"),
        {"name": RoleEnum.ADMIN},
    )
    role_id = role_row.scalar_one()

    admin = User(
        email=email,
        password_hash=hash_password(password),
        role_id=role_id,
        is_active=True,
    )
    session.add(admin)
    await session.commit()


async def run_seeds() -> None:
    async with AsyncSessionLocal() as session:
        await seed_roles(session)
        await seed_admin_user(session)
