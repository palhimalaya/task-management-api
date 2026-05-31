from fastapi import APIRouter, Query

from app.api.v1.deps.permissions import AdminDep
from app.db.session import DBSessionDep
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.user import PaginatedUsersOut, UserOut
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
    description="Returns all registered users. ADMIN only.",
    response_model=ApiResponse[PaginatedUsersOut],
)
async def list_users(
    db: DBSessionDep,
    current_user: AdminDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ApiResponse[PaginatedUsersOut]:
    users, total = await user_service.list_all_users(
        db,
        page=page,
        page_size=page_size,
    )

    data = PaginatedUsersOut(
        total=total,
        page=page,
        page_size=page_size,
        items=[UserOut.model_validate(user) for user in users],
    )

    return success(
        data=data,
        message=f"{total} user(s) found",
    )
