"""
사용자 스키마 모듈

Pydantic 모델을 사용하여 API 요청/응답의 데이터 형식을 정의한다.
스키마는 데이터 검증, 직렬화, API 문서 자동 생성에 활용된다.

계층 구조:
    UserBase: 공통 필드 정의 (기반 클래스)
    UserCreate: 사용자 생성 요청 시 사용하는 스키마
    UserUpdate: 사용자 수정 요청 시 사용하는 스키마
    UserResponse: API 응답에 사용하는 스키마
"""

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    사용자 기본 스키마

    모든 사용자 관련 스키마의 공통 필드를 정의한다.
    다른 스키마들이 이 클래스를 상속받아 중복 코드를 줄인다.
    """

    username: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="사용자 이름 (2~50자)",
        examples=["홍길동"],
    )
    email: str = Field(
        ...,
        description="이메일 주소",
        examples=["hong@example.com"],
    )


class UserCreate(UserBase):
    """
    사용자 생성 스키마

    새로운 사용자를 생성할 때 클라이언트가 전송해야 하는 데이터 형식이다.
    UserBase의 필드에 password를 추가한다.
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="비밀번호 (8자 이상)",
        examples=["securepassword123"],
    )


class UserUpdate(BaseModel):
    """
    사용자 수정 스키마

    사용자 정보를 부분 수정할 때 사용한다.
    모든 필드가 Optional이므로 변경하고 싶은 필드만 전송하면 된다.
    """

    username: str | None = Field(
        None,
        min_length=2,
        max_length=50,
        description="변경할 사용자 이름",
    )
    email: str | None = Field(
        None,
        description="변경할 이메일 주소",
    )
    password: str | None = Field(
        None,
        min_length=8,
        max_length=100,
        description="변경할 비밀번호",
    )


class UserResponse(UserBase):
    """
    사용자 응답 스키마

    API 응답 시 클라이언트에게 반환하는 데이터 형식이다.
    비밀번호 등 민감 정보는 포함하지 않는다.
    id와 is_active 필드를 추가하여 서버 측 정보를 제공한다.
    """

    id: int = Field(..., description="사용자 고유 ID")
    is_active: bool = Field(True, description="계정 활성화 상태")

    # Pydantic v2에서는 model_config를 사용한다
    # from_attributes=True로 설정하면 ORM 모델(SQLAlchemy 등)에서
    # 직접 Pydantic 모델로 변환할 수 있다
    model_config = {"from_attributes": True}
