from fastapi import Depends
from typing import Annotated

from app.api.v1.deps.auth import get_current_user
from app.core.exceptions import ForbiddenError
from app.models.user import User
from app.utils.enums import RoleEnum


def require_roles(*allowed_roles: RoleEnum):

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise ForbiddenError(
                f"This action requires one of: {', '.join(r.value for r in allowed_roles)}"
            )
        return current_user

    return _check


__all__ = ["AdminDep", "AdminOrManagerDep"]

AdminDep = Annotated[User, Depends(require_roles(RoleEnum.ADMIN))]

AdminOrManagerDep = Annotated[
    User, Depends(require_roles(RoleEnum.ADMIN, RoleEnum.MANAGER))
]
