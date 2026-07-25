from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from bet_score.application.auth import AuthenticationError
from bet_score.config import get_settings
from bet_score.domain.identity import User
from bet_score.presentation.api.dependencies import AuthServiceDependency
from bet_score.presentation.api.schemas import (
    ErrorResponse,
    TelegramAuthRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/telegram",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse}},
)
async def authenticate_telegram(
    payload: TelegramAuthRequest,
    response: Response,
    service: AuthServiceDependency,
) -> UserResponse | JSONResponse:
    try:
        session = await service.authenticate_telegram(payload.init_data)
    except AuthenticationError as error:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"code": "invalid_telegram_data", "message": str(error)},
        )

    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session.token,
        expires=session.expires_at,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
    return user_response(session.user)


@router.get(
    "/me",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse}},
)
async def get_current_user(
    request: Request,
    service: AuthServiceDependency,
) -> UserResponse | JSONResponse:
    session_token = request.cookies.get(get_settings().session_cookie_name)
    user = await service.get_user(session_token)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"code": "authentication_required", "message": "Требуется авторизация"},
        )
    return user_response(user)


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(
    request: Request,
    response: Response,
    service: AuthServiceDependency,
) -> None:
    session_token = request.cookies.get(get_settings().session_cookie_name)
    await service.sign_out(session_token)
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.secure_cookies,
        httponly=True,
        samesite="lax",
    )


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        display_name=user.display_name,
        username=user.username,
        locale=user.locale,
    )
