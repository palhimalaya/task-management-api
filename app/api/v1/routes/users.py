from fastapi import APIRouter

from app.api.v1.deps.permissions import AdminDep
from app.db.session import DBSessionDep
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.user import UserOut
from app.services import user_service
from app.utils.response import success

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)


@router.get(
    "",
    summary="List all users",
    description="Returns all registered users. **ADMIN only.**",
    response_model=ApiResponse[list[UserOut]],
)
async def list_users(
    db: DBSessionDep,
    current_user: AdminDep,
) -> ApiResponse[list[UserOut]]:
    users = await user_service.list_all_users(db)
    data = [UserOut.model_validate(u) for u in users]
    return success(data=data, message=f"{len(data)} user(s) found")
