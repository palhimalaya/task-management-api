from fastapi import APIRouter
from app.db.session import DBSessionDep
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.common import ApiResponse, ErrorResponse
from app.services import auth_service
from app.utils.response import created, success

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    summary="Register a new user",
    description=(
        "Creates a new user account with the default USER role "
        "and returns a JWT access token."
    ),
    status_code=201,
    response_model=ApiResponse[TokenResponse],
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Email already registered",
        },
    },
)
async def register(
    payload: RegisterRequest,
    db: DBSessionDep,
) -> ApiResponse[TokenResponse]:
    token = await auth_service.register_user(
        payload=payload,
        db=db,
    )

    return created(
        data=TokenResponse(
            access_token=token,
        ),
        message="User registered successfully",
    )


@router.post(
    "/login",
    summary="Login user",
    description=(
        "Authenticate using email and password " "and receive a JWT access token."
    ),
    response_model=ApiResponse[TokenResponse],
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Invalid email or password",
        },
    },
)
async def login(
    payload: LoginRequest,
    db: DBSessionDep,
) -> ApiResponse[TokenResponse]:
    token = await auth_service.login_user(
        payload=payload,
        db=db,
    )

    return success(
        data=TokenResponse(
            access_token=token,
        ),
        message="Login successful",
    )
