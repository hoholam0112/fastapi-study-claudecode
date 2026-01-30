"""
FastAPI 비동기 데이터베이스 애플리케이션

AsyncSession을 사용한 비동기 CRUD 엔드포인트를 제공합니다.
lifespan 이벤트를 통해 애플리케이션 시작 시 테이블을 자동 생성합니다.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_engine, get_db
from models import Base, User, Item


# ===========================================================================
# Pydantic 스키마 정의 (요청/응답 데이터 검증용)
# ===========================================================================


# ---------------------------------------------------------------------------
# Item 스키마
# ---------------------------------------------------------------------------
class ItemBase(BaseModel):
    """아이템 공통 필드"""
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    """아이템 생성 요청 스키마"""
    pass


class ItemResponse(ItemBase):
    """아이템 응답 스키마 - DB에서 조회된 아이템 데이터"""
    id: int
    owner_id: int

    # SQLAlchemy 모델을 Pydantic 모델로 자동 변환하기 위한 설정
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# User 스키마
# ---------------------------------------------------------------------------
class UserBase(BaseModel):
    """사용자 공통 필드"""
    email: str
    name: str


class UserCreate(UserBase):
    """사용자 생성 요청 스키마"""
    pass


class UserUpdate(BaseModel):
    """사용자 수정 요청 스키마 - 모든 필드 선택적"""
    email: str | None = None
    name: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """사용자 응답 스키마 - DB에서 조회된 사용자 데이터"""
    id: int
    is_active: bool
    items: list[ItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# 애플리케이션 라이프사이클 설정
# ===========================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 라이프사이클 관리자

    시작 시:
    - 비동기 엔진을 통해 데이터베이스 테이블을 자동 생성합니다.
    - begin() 컨텍스트 내에서 run_sync()를 사용하여
      동기 방식의 create_all()을 비동기로 실행합니다.

    종료 시:
    - 비동기 엔진의 연결 풀을 정리합니다.
    """
    # 시작: 테이블 생성
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 데이터베이스 테이블 생성 완료")

    yield  # 애플리케이션 실행 구간

    # 종료: 엔진 정리
    await async_engine.dispose()
    print("🔌 데이터베이스 연결 종료")


# ===========================================================================
# FastAPI 앱 인스턴스 생성
# ===========================================================================
app = FastAPI(
    title="비동기 데이터베이스 학습 API",
    description="SQLAlchemy 2.0 AsyncSession을 활용한 비동기 CRUD API",
    version="1.0.0",
    lifespan=lifespan,
)


# ===========================================================================
# 사용자(User) CRUD 엔드포인트
# ===========================================================================


@app.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새 사용자 생성",
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    새로운 사용자를 생성합니다.

    - 이메일 중복 검사를 수행합니다.
    - 성공 시 생성된 사용자 정보를 반환합니다.
    """
    # 이메일 중복 검사
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"이메일 '{user_data.email}'은(는) 이미 등록되어 있습니다.",
        )

    # 새 사용자 객체 생성 및 저장
    new_user = User(
        email=user_data.email,
        name=user_data.name,
    )
    db.add(new_user)
    await db.commit()

    # 커밋 후 자동 생성된 id 등의 값을 갱신
    await db.refresh(new_user)
    return new_user


@app.get(
    "/users/",
    response_model=list[UserResponse],
    summary="전체 사용자 목록 조회",
)
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    전체 사용자 목록을 페이지네이션하여 조회합니다.

    - skip: 건너뛸 레코드 수 (기본값: 0)
    - limit: 최대 조회 수 (기본값: 100)
    """
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)

    # scalars() : 결과에서 ORM 객체만 추출
    # all() : 모든 결과를 리스트로 반환
    users = result.scalars().all()
    return users


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="특정 사용자 조회",
)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 ID로 특정 사용자를 조회합니다.

    존재하지 않는 ID인 경우 404 에러를 반환합니다.
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"사용자 ID {user_id}을(를) 찾을 수 없습니다.",
        )
    return user


@app.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="사용자 정보 수정",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 정보를 부분 수정합니다.

    - 전달된 필드만 업데이트됩니다 (None이 아닌 필드만 반영).
    - 이메일 변경 시 중복 검사를 수행합니다.
    """
    # 수정 대상 사용자 조회
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"사용자 ID {user_id}을(를) 찾을 수 없습니다.",
        )

    # 이메일 변경 시 중복 검사
    if user_data.email is not None and user_data.email != user.email:
        email_check = select(User).where(User.email == user_data.email)
        email_result = await db.execute(email_check)
        if email_result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이메일 '{user_data.email}'은(는) 이미 사용 중입니다.",
            )

    # None이 아닌 필드만 업데이트 (부분 수정 지원)
    update_fields = user_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="사용자 삭제",
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    사용자를 삭제합니다.

    - cascade 설정으로 해당 사용자의 아이템도 함께 삭제됩니다.
    - 성공 시 204 No Content를 반환합니다.
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"사용자 ID {user_id}을(를) 찾을 수 없습니다.",
        )

    await db.delete(user)
    await db.commit()


# ===========================================================================
# 아이템(Item) CRUD 엔드포인트
# ===========================================================================


@app.post(
    "/users/{user_id}/items/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="아이템 생성",
)
async def create_item_for_user(
    user_id: int,
    item_data: ItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    특정 사용자에게 새로운 아이템을 추가합니다.

    - 먼저 사용자가 존재하는지 확인합니다.
    - 아이템의 owner_id를 해당 사용자의 ID로 설정합니다.
    """
    # 소유자(사용자) 존재 여부 확인
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"사용자 ID {user_id}을(를) 찾을 수 없습니다.",
        )

    # 새 아이템 생성
    new_item = Item(
        title=item_data.title,
        description=item_data.description,
        owner_id=user_id,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


@app.get(
    "/items/",
    response_model=list[ItemResponse],
    summary="전체 아이템 목록 조회",
)
async def read_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    전체 아이템 목록을 페이지네이션하여 조회합니다.
    """
    stmt = select(Item).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return items


@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="특정 아이템 조회",
)
async def read_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    아이템 ID로 특정 아이템을 조회합니다.
    """
    stmt = select(Item).where(Item.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아이템 ID {item_id}을(를) 찾을 수 없습니다.",
        )
    return item


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="아이템 삭제",
)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    아이템을 삭제합니다.
    """
    stmt = select(Item).where(Item.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아이템 ID {item_id}을(를) 찾을 수 없습니다.",
        )

    await db.delete(item)
    await db.commit()


# ===========================================================================
# 헬스 체크 엔드포인트
# ===========================================================================


@app.get("/health", summary="서버 상태 확인")
async def health_check():
    """서버 및 데이터베이스 연결 상태를 확인합니다."""
    return {"status": "healthy", "message": "비동기 데이터베이스 서버가 정상 동작 중입니다."}
