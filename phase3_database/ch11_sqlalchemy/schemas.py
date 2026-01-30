"""
schemas.py - Pydantic 스키마 (API 요청/응답 데이터 검증)

이 파일은 API를 통해 주고받는 데이터의 형태(shape)를 정의합니다.
models.py가 "DB에 어떻게 저장할 것인가"를 정의한다면,
schemas.py는 "API에서 어떤 데이터를 주고받을 것인가"를 정의합니다.

스키마 설계 패턴:
    - Base: 공통 필드 정의 (읽기/쓰기 공통)
    - Create: 생성 시 필요한 추가 필드 (예: 비밀번호)
    - Read(응답): DB에서 읽어온 후 반환할 필드 (예: id, 관계 데이터)

이렇게 분리하면 같은 엔티티라도 상황에 맞는 데이터만 노출할 수 있습니다.
예) 사용자 생성 시에는 password를 받지만, 응답에는 password를 포함하지 않음
"""

from pydantic import BaseModel


# ============================================================
# Item(아이템) 관련 스키마
# ============================================================

class ItemBase(BaseModel):
    """
    아이템 기본 스키마 - 읽기/쓰기에 공통으로 사용되는 필드

    - title: 아이템 제목 (필수)
    - description: 아이템 설명 (선택, 기본값 None)
    """
    title: str
    description: str | None = None  # Python 3.10+ 유니온 타입 표기


class ItemCreate(ItemBase):
    """
    아이템 생성 스키마 - POST 요청 시 클라이언트가 보내는 데이터

    현재는 ItemBase와 동일하지만, 추후 생성 시에만 필요한
    필드가 있다면 여기에 추가합니다.
    (예: 초기 수량, 카테고리 등)
    """
    pass


class Item(ItemBase):
    """
    아이템 응답 스키마 - API 응답으로 클라이언트에게 반환하는 데이터

    ItemBase의 필드에 더해 DB에서 자동 생성되는 필드를 포함합니다:
    - id: 데이터베이스가 자동 부여한 고유 식별자
    - owner_id: 이 아이템을 소유한 사용자의 ID
    """
    id: int
    owner_id: int

    # model_config를 사용하여 ORM 모드를 활성화합니다.
    # Pydantic v2에서는 from_attributes=True를 사용합니다.
    # (Pydantic v1에서는 orm_mode=True를 사용했습니다)
    #
    # 이 설정이 없으면 SQLAlchemy 모델 객체를 Pydantic 스키마로
    # 변환할 수 없습니다. ORM 객체의 속성(attribute)에서
    # 데이터를 읽어오려면 반드시 이 설정이 필요합니다.
    #
    # 작동 원리:
    #   일반 모드: dict에서만 데이터 읽기 → {"id": 1, "title": "..."}
    #   ORM 모드: 객체 속성에서도 읽기 → item.id, item.title
    model_config = {"from_attributes": True}


# ============================================================
# User(사용자) 관련 스키마
# ============================================================

class UserBase(BaseModel):
    """
    사용자 기본 스키마 - 읽기/쓰기에 공통으로 사용되는 필드

    - email: 사용자 이메일 (필수)
    """
    email: str


class UserCreate(UserBase):
    """
    사용자 생성 스키마 - POST 요청 시 클라이언트가 보내는 데이터

    UserBase의 email에 더해 password 필드가 추가됩니다.
    비밀번호는 생성할 때만 받고, 응답에서는 절대 반환하지 않습니다.

    주의: 이 스키마의 'password'는 평문(plain text)입니다.
    서버에서 반드시 해시 처리한 후 DB에 저장해야 합니다.
    """
    password: str


class User(UserBase):
    """
    사용자 응답 스키마 - API 응답으로 클라이언트에게 반환하는 데이터

    UserBase의 email에 더해 다음 필드를 포함합니다:
    - id: 데이터베이스가 자동 부여한 고유 식별자
    - is_active: 계정 활성화 여부
    - items: 이 사용자가 소유한 아이템 목록

    중요: hashed_password는 포함하지 않습니다!
    응답 스키마에 비밀번호 관련 필드를 넣으면 보안 위험이 발생합니다.
    """
    id: int
    is_active: bool

    # 사용자가 소유한 아이템 목록 (1:N 관계 데이터)
    # List[Item]으로 선언하면 사용자 조회 시 관련 아이템도 함께 반환됩니다.
    # 여기서 Item은 위에서 정의한 Pydantic Item 스키마입니다.
    items: list[Item] = []

    # ORM 모드 활성화 (SQLAlchemy 모델 → Pydantic 스키마 변환 허용)
    model_config = {"from_attributes": True}
