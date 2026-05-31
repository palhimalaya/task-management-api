from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import DBSessionDep
from app.models.user import User

_bearer = HTTPBearer()


async def get_current_user(
    db: DBSessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("Invalid token payload")
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")

    user = await db.scalar(
        select(User).options(selectinload(User.role)).where(User.id == int(user_id))
    )
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or account disabled")

    return user


CurrentUserDep = Annotated[
    User,
    Depends(get_current_user),
]
