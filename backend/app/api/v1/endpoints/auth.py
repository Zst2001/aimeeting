from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_auth_service, get_current_user
from app.core.logging import request_id_context
from app.db.models.user import User
from app.schemas.auth import (
    ApiSuccessLoginResponse,
    ApiSuccessRefreshResponse,
    LoginData,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenPairResponse,
)
from app.schemas.user import login_user_response
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiSuccessLoginResponse)
def login(request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> dict[str, object]:
    user, tokens = auth_service.login(username=request.username, password=request.password)
    return {
        "code": 0,
        "message": "ok",
        "data": LoginData(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
            user=login_user_response(user),
        ),
        "request_id": request_id_context.get(),
    }


@router.post("/refresh", response_model=ApiSuccessRefreshResponse)
def refresh(request: RefreshRequest, auth_service: AuthService = Depends(get_auth_service)) -> dict[str, object]:
    tokens = auth_service.refresh(refresh_token=request.refresh_token)
    return {
        "code": 0,
        "message": "ok",
        "data": TokenPairResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        ),
        "request_id": request_id_context.get(),
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    auth_service.logout(refresh_token=request.refresh_token, expected_user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
