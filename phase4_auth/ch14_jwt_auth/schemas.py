"""
schemas.py - Pydantic 모델 정의

JWT 인증에 필요한 요청/응답 스키마를 정의한다.
각 모델은 데이터 유효성 검사와 직렬화/역직렬화를 담당한다.
"""

from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# 토큰 관련 스키마
# ============================================================

class Token(BaseModel):
    """
    토큰 응답 모델

    로그인 성공 시 클라이언트에게 반환되는 토큰 정보.
    OAuth2 사양에 따라 access_token과 token_type을 포함한다.
    """
    access_token: str = Field(
        ...,
        description="JWT 액세스 토큰",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        ...,
        description="토큰 타입 (항상 'bearer')",
        examples=["bearer"],
    )


class TokenData(BaseModel):
    """
    토큰 페이로드 데이터 모델

    JWT 토큰을 디코딩한 후 추출되는 사용자 식별 정보.
    토큰 검증 과정에서 내부적으로 사용된다.
    """
    username: Optional[str] = Field(
        default=None,
        description="토큰에 포함된 사용자명 (sub 클레임)",
    )


# ============================================================
# 사용자 관련 스키마
# ============================================================

class UserCreate(BaseModel):
    """
    회원가입 요청 모델

    새로운 사용자를 등록할 때 클라이언트가 전송하는 데이터.
    비밀번호는 평문으로 전달되며, 서버에서 해싱하여 저장한다.
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="사용자명 (3~50자)",
        examples=["testuser"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="비밀번호 (6자 이상)",
        examples=["mypassword123"],
    )


class User(BaseModel):
    """
    사용자 응답 모델

    API 응답으로 반환되는 사용자 정보.
    비밀번호 등 민감한 정보는 포함하지 않는다.
    """
    username: str = Field(
        ...,
        description="사용자명",
        examples=["testuser"],
    )
    email: Optional[str] = Field(
        default=None,
        description="이메일 주소 (선택 사항)",
        examples=["user@example.com"],
    )
    disabled: bool = Field(
        default=False,
        description="계정 비활성화 여부 (True이면 로그인 불가)",
    )


class UserInDB(User):
    """
    데이터베이스 사용자 모델

    User 모델을 상속하며, 해싱된 비밀번호를 추가로 포함한다.
    이 모델은 서버 내부에서만 사용하며, 절대 클라이언트에게 반환하지 않는다.
    """
    hashed_password: str = Field(
        ...,
        description="bcrypt로 해싱된 비밀번호",
    )
