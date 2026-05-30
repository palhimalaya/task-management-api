from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import LoginRequest, RegisterRequest
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User

from app.models.role import Role
from app.core.exceptions import ConflictError
from sqlalchemy import select
from app.utils.enums import RoleEnum


async def register_user(
    payload: RegisterRequest,
    db: AsyncSession,
) -> str:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise ConflictError("Email is already registered")

    role = await db.scalar(select(Role).where(Role.name == RoleEnum.USER))
    if role is None:
        raise RuntimeError("Default USER role not found — run database seeding first")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=role.id,
    )

    db.add(user)
    await db.flush()

    return create_access_token(subject=user.id)


async def login_user(
    payload: LoginRequest,
    db: AsyncSession,
) -> str:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not user.is_active:
        raise ConflictError("Invalid email or password")

    if not user.password_hash or not verify_password(
        payload.password, user.password_hash
    ):
        raise ConflictError("Invalid email or password")

    return create_access_token(subject=user.id)
