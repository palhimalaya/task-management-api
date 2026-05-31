from typing import Any


def success(
    data: Any = None,
    message: str = "Success",
) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def created(
    data: Any = None,
    message: str = "Created successfully",
) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
    }
