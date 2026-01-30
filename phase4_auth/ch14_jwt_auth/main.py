"""
main.py - FastAPI JWT 인증 애플리케이션

회원가입, 로그인(토큰 발급), 보호된 API 엔드포인트를 제공한다.
uvicorn main:app --reload 명령으로 실행한다.
"""

from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_active_user,
    get_password_hash,
    get_user,
)
from schemas import Token, User, UserCreate


# ============================================================
# FastAPI 앱 인스턴스 생성
# ============================================================

app = FastAPI(
    title="JWT 인증 학습 API",
    description=(
        "FastAPI와 JWT를 활용한 토큰 기반 인증 시스템 예제입니다.\n\n"
        "**테스트 순서:** 회원가입 -> 로그인(토큰 발급) -> 보호된 API 접근\n\n"
        "Swagger UI 상단의 **Authorize** 버튼을 클릭하여 로그인할 수 있습니다."
    ),
    version="1.0.0",
)


# ============================================================
# 엔드포인트 정의
# ============================================================

@app.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    tags=["인증"],
)
async def register(user_data: UserCreate):
    """
    새로운 사용자를 등록한다.

    - 사용자명 중복 여부를 검사한다.
    - 비밀번호를 bcrypt로 해싱하여 저장한다.
    - 실제 운영 환경에서는 데이터베이스에 저장해야 한다.
    """
    # 사용자명 중복 검사
    if user_data.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 사용자명입니다.",
        )

    # 비밀번호를 해싱하여 인메모리 DB에 저장
    hashed_password = get_password_hash(user_data.password)
    fake_users_db[user_data.username] = {
        "username": user_data.username,
        "email": None,
        "disabled": False,
        "hashed_password": hashed_password,
    }

    return {
        "message": "회원가입이 완료되었습니다.",
        "username": user_data.username,
    }


@app.post(
    "/token",
    response_model=Token,
    summary="로그인 (토큰 발급)",
    tags=["인증"],
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    사용자 인증 후 JWT 액세스 토큰을 발급한다.

    - OAuth2 사양에 따라 `application/x-www-form-urlencoded` 형식으로 요청한다.
    - `username`과 `password` 필드를 form data로 전송한다.
    - 인증 성공 시 Bearer 타입의 JWT 토큰을 반환한다.
    """
    # 사용자 인증 (사용자명 + 비밀번호 검증)
    user = authenticate_user(
        fake_users_db,
        form_data.username,
        form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자명 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWT 액세스 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@app.get(
    "/users/me",
    response_model=User,
    summary="현재 사용자 정보 조회",
    tags=["사용자"],
)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
):
    """
    현재 인증된 사용자의 정보를 반환한다.

    - Authorization 헤더에 유효한 JWT 토큰이 필요하다.
    - 형식: `Authorization: Bearer <access_token>`
    - 비활성화된 계정은 접근할 수 없다.
    """
    return current_user


@app.get(
    "/protected",
    response_model=dict,
    summary="보호된 엔드포인트",
    tags=["사용자"],
)
async def protected_route(
    current_user: User = Depends(get_current_active_user),
):
    """
    인증된 사용자만 접근할 수 있는 보호된 엔드포인트 예제.

    - 이 엔드포인트는 인증 의존성이 적용되어 있다.
    - 유효한 토큰 없이 접근하면 401 Unauthorized 에러가 반환된다.
    """
    return {
        "message": "이 엔드포인트는 인증된 사용자만 접근할 수 있습니다.",
        "user": current_user.username,
    }
