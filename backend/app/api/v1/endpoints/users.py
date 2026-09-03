from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.core.logging import request_id_context
from app.db.models.user import User
from app.schemas.auth import ApiSuccessCurrentUserResponse
from app.schemas.user import current_user_response


router = APIRouter(tags=["users"])


@router.get("/me", response_model=ApiSuccessCurrentUserResponse)
def me(current_user: User = Depends(get_current_user)) -> dict[str, object]:
    return {
        "code": 0,
        "message": "ok",
        "data": current_user_response(current_user),
        "request_id": request_id_context.get(),
    }
