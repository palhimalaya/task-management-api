from typing import Any

from fastapi.responses import JSONResponse


def success(
    data: Any = None, message: str = "Success", status_code: int = 200
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data},
    )


def created(data: Any = None, message: str = "Created successfully") -> JSONResponse:
    return success(data=data, message=message, status_code=201)
