"""
Chapter 24: API 문서화와 버전 관리

OpenAPI 스펙 커스터마이징, Tags 구성, API 버전 관리(URL/Header/Query),
Swagger UI 커스터마이징을 학습한다.

실행 방법:
    pip install fastapi uvicorn
    uvicorn main:app --reload
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

# ============================================================
# 1. Tags 메타데이터 정의
# ============================================================

# Swagger UI에서 엔드포인트를 그룹화할 태그 목록
# 여기 정의한 순서대로 Swagger UI에 표시된다
tags_metadata = [
    {
        "name": "기본",
        "description": "루트 및 서비스 기본 정보 엔드포인트",
    },
    {
        "name": "v1 - 사용자",
        "description": "**API V1** - 사용자 관리 엔드포인트 (초기 버전)",
        "externalDocs": {
            "description": "사용자 API 상세 가이드",
            "url": "https://example.com/docs/users",
        },
    },
    {
        "name": "v1 - 상품",
        "description": "**API V1** - 상품 관리 엔드포인트 (초기 버전)",
    },
    {
        "name": "v2 - 사용자",
        "description": "**API V2** - 사용자 관리 엔드포인트 (개선 버전). "
        "페이지네이션, 정렬 기능이 추가되었다.",
    },
    {
        "name": "v2 - 상품",
        "description": "**API V2** - 상품 관리 엔드포인트 (개선 버전). "
        "카테고리 필터링, 가격 범위 검색이 추가되었다.",
    },
    {
        "name": "버전 관리 (헤더/쿼리)",
        "description": "헤더 기반, 쿼리 파라미터 기반 버전 관리 예시",
    },
]

# ============================================================
# 2. FastAPI 앱 생성 (메타데이터 커스터마이징)
# ============================================================

# API 상세 설명 (Markdown 문법 사용 가능)
api_description = """
## FastAPI 문서화와 버전 관리 학습 API

이 API는 FastAPI의 문서화 기능과 버전 관리 전략을 학습하기 위한
예제 프로젝트입니다.

### 주요 기능

* **OpenAPI 스펙 커스터마이징** - 메타데이터, 태그, 응답 설명 설정
* **API 버전 관리** - URL 경로, HTTP 헤더, 쿼리 파라미터 방식 비교
* **Swagger UI 활용** - 인터랙티브 API 테스트 환경

### 버전 정보

| 버전 | 상태 | 비고 |
|------|------|------|
| V1 | 유지보수 | 기본 CRUD |
| V2 | 활성 | 페이지네이션, 필터링 추가 |
"""

app = FastAPI(
    title="Chapter 24: API 문서화와 버전 관리",
    description=api_description,
    version="2.0.0",
    terms_of_service="https://example.com/terms",
    contact={
        "name": "FastAPI 학습 프로젝트",
        "url": "https://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=tags_metadata,
    # Swagger UI 경로 커스터마이징 (기본값 유지)
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================
# 3. Pydantic 모델 정의 (요청/응답 스키마)
# ============================================================


# --- V1 모델 ---

class UserCreateV1(BaseModel):
    """V1 사용자 생성 요청 모델"""

    name: str = Field(..., min_length=1, max_length=50, examples=["홍길동"], description="사용자 이름")
    email: str = Field(..., examples=["hong@example.com"], description="이메일 주소")

    model_config = {"json_schema_extra": {"examples": [{"name": "홍길동", "email": "hong@example.com"}]}}


class UserResponseV1(BaseModel):
    """V1 사용자 응답 모델"""

    id: int = Field(..., description="사용자 고유 ID")
    name: str = Field(..., description="사용자 이름")
    email: str = Field(..., description="이메일 주소")


class ProductResponseV1(BaseModel):
    """V1 상품 응답 모델"""

    id: int = Field(..., description="상품 고유 ID")
    name: str = Field(..., description="상품명")
    price: int = Field(..., description="가격 (원)")


# --- V2 모델 (개선된 버전) ---

class UserCreateV2(BaseModel):
    """V2 사용자 생성 요청 모델 (추가 필드 포함)"""

    name: str = Field(..., min_length=1, max_length=50, examples=["홍길동"], description="사용자 이름")
    email: str = Field(..., examples=["hong@example.com"], description="이메일 주소")
    nickname: Optional[str] = Field(None, max_length=30, description="닉네임 (선택)")
    bio: Optional[str] = Field(None, max_length=200, description="자기소개 (선택)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "홍길동",
                    "email": "hong@example.com",
                    "nickname": "길동이",
                    "bio": "FastAPI를 공부하고 있습니다.",
                }
            ]
        }
    }


class UserResponseV2(BaseModel):
    """V2 사용자 응답 모델 (추가 필드 포함)"""

    id: int = Field(..., description="사용자 고유 ID")
    name: str = Field(..., description="사용자 이름")
    email: str = Field(..., description="이메일 주소")
    nickname: Optional[str] = Field(None, description="닉네임")
    bio: Optional[str] = Field(None, description="자기소개")
    created_at: str = Field(..., description="계정 생성 시간 (ISO 8601)")


class ProductResponseV2(BaseModel):
    """V2 상품 응답 모델 (카테고리, 재고 추가)"""

    id: int = Field(..., description="상품 고유 ID")
    name: str = Field(..., description="상품명")
    price: int = Field(..., description="가격 (원)")
    category: str = Field(..., description="상품 카테고리")
    stock: int = Field(..., description="재고 수량")
    created_at: str = Field(..., description="등록 시간 (ISO 8601)")


class PaginatedResponse(BaseModel):
    """페이지네이션 응답 래퍼 모델"""

    items: list = Field(..., description="데이터 목록")
    total: int = Field(..., description="전체 항목 수")
    page: int = Field(..., description="현재 페이지 번호")
    size: int = Field(..., description="페이지당 항목 수")
    pages: int = Field(..., description="전체 페이지 수")


class ErrorResponse(BaseModel):
    """공통 에러 응답 모델"""

    detail: str = Field(..., description="에러 상세 메시지")
    error_code: Optional[str] = Field(None, description="에러 코드")


# ============================================================
# 4. 시뮬레이션 데이터
# ============================================================

# 메모리 기반 샘플 데이터 (실제 환경에서는 DB 사용)
SAMPLE_USERS = [
    {"id": 1, "name": "홍길동", "email": "hong@example.com", "nickname": "길동이", "bio": "조선시대 의적"},
    {"id": 2, "name": "김철수", "email": "kim@example.com", "nickname": "철수", "bio": "개발자"},
    {"id": 3, "name": "이영희", "email": "lee@example.com", "nickname": "영희", "bio": "디자이너"},
]

SAMPLE_PRODUCTS = [
    {"id": 1, "name": "노트북", "price": 1500000, "category": "전자기기", "stock": 25},
    {"id": 2, "name": "키보드", "price": 120000, "category": "주변기기", "stock": 100},
    {"id": 3, "name": "모니터", "price": 450000, "category": "전자기기", "stock": 15},
    {"id": 4, "name": "마우스", "price": 80000, "category": "주변기기", "stock": 200},
    {"id": 5, "name": "헤드셋", "price": 250000, "category": "주변기기", "stock": 50},
]

# ============================================================
# 5. API V1 라우터 (URL 경로 기반 버전 관리)
# ============================================================

# V1 라우터: /api/v1 경로 접두사
v1_router = APIRouter(prefix="/api/v1")


@v1_router.get(
    "/users",
    tags=["v1 - 사용자"],
    response_model=list[UserResponseV1],
    summary="전체 사용자 목록 조회",
    response_description="사용자 목록이 배열 형태로 반환됩니다",
)
async def v1_get_users():
    """
    V1 사용자 전체 목록을 조회한다.

    페이지네이션 없이 전체 목록을 반환하는 기본 버전이다.
    대량 데이터 처리가 필요한 경우 V2 API 사용을 권장한다.
    """
    return [
        UserResponseV1(id=u["id"], name=u["name"], email=u["email"])
        for u in SAMPLE_USERS
    ]


@v1_router.get(
    "/users/{user_id}",
    tags=["v1 - 사용자"],
    response_model=UserResponseV1,
    summary="특정 사용자 조회",
    responses={
        200: {"description": "사용자 정보 조회 성공"},
        404: {
            "description": "사용자를 찾을 수 없음",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "사용자를 찾을 수 없습니다", "error_code": "USER_NOT_FOUND"}
                }
            },
        },
    },
)
async def v1_get_user(user_id: int):
    """
    사용자 ID로 특정 사용자의 정보를 조회한다.

    - **user_id**: 조회할 사용자의 고유 ID (정수)
    """
    # 샘플 데이터에서 사용자 검색
    user = next((u for u in SAMPLE_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return UserResponseV1(id=user["id"], name=user["name"], email=user["email"])


@v1_router.post(
    "/users",
    tags=["v1 - 사용자"],
    response_model=UserResponseV1,
    status_code=201,
    summary="새 사용자 생성",
    responses={
        201: {"description": "사용자 생성 성공"},
        422: {"description": "요청 데이터 유효성 검증 실패"},
    },
)
async def v1_create_user(user: UserCreateV1):
    """
    새로운 사용자를 생성한다.

    - **name**: 사용자 이름 (1~50자)
    - **email**: 이메일 주소
    """
    # 새 ID 생성 (시뮬레이션)
    new_id = max(u["id"] for u in SAMPLE_USERS) + 1 if SAMPLE_USERS else 1
    new_user = {"id": new_id, "name": user.name, "email": user.email}
    SAMPLE_USERS.append({**new_user, "nickname": None, "bio": None})
    return UserResponseV1(**new_user)


@v1_router.get(
    "/users/search",
    tags=["v1 - 사용자"],
    response_model=list[UserResponseV1],
    summary="사용자 이름 검색 (폐기 예정)",
    deprecated=True,  # Swagger UI에서 취소선으로 표시됨
    responses={
        200: {"description": "검색 결과 반환"},
    },
)
async def v1_search_users(name: str = Query(..., description="검색할 사용자 이름")):
    """
    **[폐기 예정]** 사용자 이름으로 검색한다.

    이 엔드포인트는 V2의 개선된 검색 API로 대체될 예정이다.
    V2 API (`/api/v2/users?search=...`)를 사용하는 것을 권장한다.

    > **주의**: 이 엔드포인트는 향후 버전에서 제거됩니다.
    """
    # 이름에 검색어가 포함된 사용자를 찾는다
    results = [u for u in SAMPLE_USERS if name in u["name"]]
    return [
        UserResponseV1(id=u["id"], name=u["name"], email=u["email"])
        for u in results
    ]


@v1_router.get(
    "/products",
    tags=["v1 - 상품"],
    response_model=list[ProductResponseV1],
    summary="전체 상품 목록 조회",
)
async def v1_get_products():
    """
    V1 상품 전체 목록을 조회한다.

    카테고리 필터링이나 페이지네이션 없이 전체 목록을 반환한다.
    """
    return [
        ProductResponseV1(id=p["id"], name=p["name"], price=p["price"])
        for p in SAMPLE_PRODUCTS
    ]


@v1_router.get(
    "/products/{product_id}",
    tags=["v1 - 상품"],
    response_model=ProductResponseV1,
    summary="특정 상품 조회",
    responses={
        200: {"description": "상품 정보 조회 성공"},
        404: {"description": "상품을 찾을 수 없음"},
    },
)
async def v1_get_product(product_id: int):
    """
    상품 ID로 특정 상품의 정보를 조회한다.

    - **product_id**: 조회할 상품의 고유 ID (정수)
    """
    product = next((p for p in SAMPLE_PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return ProductResponseV1(id=product["id"], name=product["name"], price=product["price"])


# ============================================================
# 6. API V2 라우터 (개선된 버전)
# ============================================================

# V2 라우터: /api/v2 경로 접두사
v2_router = APIRouter(prefix="/api/v2")


@v2_router.get(
    "/users",
    tags=["v2 - 사용자"],
    response_model=PaginatedResponse,
    summary="사용자 목록 조회 (페이지네이션 지원)",
    response_description="페이지네이션 정보와 함께 사용자 목록이 반환됩니다",
)
async def v2_get_users(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(10, ge=1, le=100, description="페이지당 항목 수 (최대 100)"),
    search: Optional[str] = Query(None, description="이름 검색어 (선택)"),
):
    """
    V2 사용자 목록을 페이지네이션과 함께 조회한다.

    V1 대비 개선 사항:
    - **페이지네이션**: `page`와 `size` 파라미터로 결과를 나누어 조회
    - **검색 기능**: `search` 파라미터로 이름 기반 필터링
    - **추가 필드**: 닉네임, 자기소개, 생성 시간 포함
    """
    now = datetime.now(timezone.utc).isoformat()

    # 검색어 필터링
    filtered = SAMPLE_USERS
    if search:
        filtered = [u for u in filtered if search in u["name"]]

    # 전체 항목 수
    total = len(filtered)

    # 페이지네이션 적용
    start = (page - 1) * size
    end = start + size
    page_items = filtered[start:end]

    # V2 응답 모델로 변환 (추가 필드 포함)
    items = [
        UserResponseV2(
            id=u["id"],
            name=u["name"],
            email=u["email"],
            nickname=u.get("nickname"),
            bio=u.get("bio"),
            created_at=now,
        )
        for u in page_items
    ]

    # 전체 페이지 수 계산
    pages = (total + size - 1) // size

    return PaginatedResponse(
        items=[item.model_dump() for item in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@v2_router.get(
    "/users/{user_id}",
    tags=["v2 - 사용자"],
    response_model=UserResponseV2,
    summary="특정 사용자 상세 조회",
    responses={
        200: {"description": "사용자 상세 정보 조회 성공"},
        404: {
            "description": "사용자를 찾을 수 없음",
            "model": ErrorResponse,
        },
    },
)
async def v2_get_user(user_id: int):
    """
    V2 사용자 상세 정보를 조회한다.

    V1 대비 추가된 필드:
    - **nickname**: 사용자 닉네임
    - **bio**: 자기소개
    - **created_at**: 계정 생성 시간

    - **user_id**: 조회할 사용자의 고유 ID (정수)
    """
    user = next((u for u in SAMPLE_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return UserResponseV2(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        nickname=user.get("nickname"),
        bio=user.get("bio"),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@v2_router.post(
    "/users",
    tags=["v2 - 사용자"],
    response_model=UserResponseV2,
    status_code=201,
    summary="새 사용자 생성 (확장 필드 포함)",
    responses={
        201: {"description": "사용자 생성 성공"},
        422: {"description": "요청 데이터 유효성 검증 실패"},
    },
)
async def v2_create_user(user: UserCreateV2):
    """
    V2 사용자를 생성한다.

    V1 대비 추가된 입력 필드:
    - **nickname**: 닉네임 (선택, 최대 30자)
    - **bio**: 자기소개 (선택, 최대 200자)
    """
    now = datetime.now(timezone.utc).isoformat()
    new_id = max(u["id"] for u in SAMPLE_USERS) + 1 if SAMPLE_USERS else 1
    new_user = {
        "id": new_id,
        "name": user.name,
        "email": user.email,
        "nickname": user.nickname,
        "bio": user.bio,
    }
    SAMPLE_USERS.append(new_user)
    return UserResponseV2(**new_user, created_at=now)


@v2_router.get(
    "/products",
    tags=["v2 - 상품"],
    response_model=PaginatedResponse,
    summary="상품 목록 조회 (필터링, 페이지네이션 지원)",
)
async def v2_get_products(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
    category: Optional[str] = Query(None, description="카테고리 필터 (예: 전자기기, 주변기기)"),
    min_price: Optional[int] = Query(None, ge=0, description="최소 가격 (원)"),
    max_price: Optional[int] = Query(None, ge=0, description="최대 가격 (원)"),
):
    """
    V2 상품 목록을 필터링 및 페이지네이션과 함께 조회한다.

    V1 대비 개선 사항:
    - **카테고리 필터링**: `category` 파라미터로 특정 카테고리만 조회
    - **가격 범위 검색**: `min_price`, `max_price`로 가격 범위 지정
    - **페이지네이션**: 대량 데이터 처리 지원
    - **추가 필드**: 카테고리, 재고, 등록 시간 포함
    """
    now = datetime.now(timezone.utc).isoformat()

    # 필터링 적용
    filtered = SAMPLE_PRODUCTS
    if category:
        filtered = [p for p in filtered if p["category"] == category]
    if min_price is not None:
        filtered = [p for p in filtered if p["price"] >= min_price]
    if max_price is not None:
        filtered = [p for p in filtered if p["price"] <= max_price]

    total = len(filtered)

    # 페이지네이션 적용
    start = (page - 1) * size
    end = start + size
    page_items = filtered[start:end]

    items = [
        ProductResponseV2(
            id=p["id"],
            name=p["name"],
            price=p["price"],
            category=p["category"],
            stock=p["stock"],
            created_at=now,
        )
        for p in page_items
    ]

    pages = (total + size - 1) // size

    return PaginatedResponse(
        items=[item.model_dump() for item in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@v2_router.get(
    "/products/{product_id}",
    tags=["v2 - 상품"],
    response_model=ProductResponseV2,
    summary="특정 상품 상세 조회",
    responses={
        200: {"description": "상품 상세 정보 조회 성공"},
        404: {"description": "상품을 찾을 수 없음"},
    },
)
async def v2_get_product(product_id: int):
    """
    V2 상품 상세 정보를 조회한다.

    V1 대비 추가된 필드:
    - **category**: 상품 카테고리
    - **stock**: 재고 수량
    - **created_at**: 상품 등록 시간
    """
    product = next((p for p in SAMPLE_PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return ProductResponseV2(
        id=product["id"],
        name=product["name"],
        price=product["price"],
        category=product["category"],
        stock=product["stock"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================
# 7. 헤더/쿼리 기반 버전 관리 예시
# ============================================================


@app.get(
    "/api/version-by-header",
    tags=["버전 관리 (헤더/쿼리)"],
    summary="헤더 기반 API 버전 관리 예시",
    responses={
        200: {"description": "요청한 버전에 맞는 응답 반환"},
    },
)
async def version_by_header(
    x_api_version: str = Header("1", description="API 버전 (1 또는 2)"),
):
    """
    HTTP 헤더(`X-Api-Version`)로 API 버전을 지정하는 방식의 예시.

    요청 예시:
    ```
    curl -H "X-Api-Version: 2" http://localhost:8000/api/version-by-header
    ```

    **장점**: URL이 깔끔하고 REST 원칙에 부합
    **단점**: 브라우저에서 직접 테스트하기 어려움
    """
    if x_api_version == "2":
        return {
            "version": "v2",
            "message": "V2 응답입니다. 개선된 기능이 포함되어 있습니다.",
            "features": ["pagination", "filtering", "extended_fields"],
        }
    else:
        return {
            "version": "v1",
            "message": "V1 응답입니다. 기본 기능만 제공합니다.",
            "features": ["basic_crud"],
        }


@app.get(
    "/api/version-by-query",
    tags=["버전 관리 (헤더/쿼리)"],
    summary="쿼리 파라미터 기반 API 버전 관리 예시",
    responses={
        200: {"description": "요청한 버전에 맞는 응답 반환"},
    },
)
async def version_by_query(
    version: str = Query("1", description="API 버전 (1 또는 2)"),
):
    """
    쿼리 파라미터(`?version=2`)로 API 버전을 지정하는 방식의 예시.

    요청 예시:
    ```
    curl "http://localhost:8000/api/version-by-query?version=2"
    ```

    **장점**: 구현이 간단하고 브라우저에서 바로 테스트 가능
    **단점**: URL이 복잡해지고 캐싱이 어려워질 수 있음
    """
    if version == "2":
        return {
            "version": "v2",
            "message": "V2 응답입니다. 쿼리 파라미터로 버전을 선택했습니다.",
            "features": ["pagination", "filtering", "extended_fields"],
        }
    else:
        return {
            "version": "v1",
            "message": "V1 응답입니다. 쿼리 파라미터로 버전을 선택했습니다.",
            "features": ["basic_crud"],
        }


# ============================================================
# 8. 라우터 등록
# ============================================================

# V1, V2 라우터를 메인 앱에 등록
app.include_router(v1_router)
app.include_router(v2_router)


# ============================================================
# 9. 루트 엔드포인트
# ============================================================


@app.get(
    "/",
    tags=["기본"],
    summary="API 루트",
    response_description="API 안내 정보가 반환됩니다",
)
async def root():
    """
    API 루트 엔드포인트.

    사용 가능한 API 버전과 문서 링크를 안내한다.
    """
    return {
        "message": "Chapter 24: API 문서화와 버전 관리 학습 API",
        "api_versions": {
            "v1": "/api/v1 (기본 CRUD)",
            "v2": "/api/v2 (페이지네이션, 필터링 추가)",
        },
        "docs": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        },
        "version_strategies": {
            "url_path": "/api/v1/... 또는 /api/v2/...",
            "header": "/api/version-by-header (X-Api-Version 헤더)",
            "query": "/api/version-by-query?version=1",
        },
    }


# ============================================================
# 10. OpenAPI 스키마 커스터마이징
# ============================================================


def custom_openapi():
    """
    OpenAPI 스키마를 커스터마이징하는 함수.

    FastAPI가 자동 생성한 스키마에 추가 정보를 삽입한다.
    이 함수는 최초 1회만 실행되고 이후에는 캐시된 결과를 반환한다.
    """
    # 이미 생성된 스키마가 있으면 캐시된 것을 반환
    if app.openapi_schema:
        return app.openapi_schema

    # FastAPI 기본 스키마 생성
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
    )

    # 커스텀 확장 필드 추가 (x- 접두사는 OpenAPI 확장 규격)
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png",
        "altText": "FastAPI 학습 프로젝트 로고",
    }

    # API 서버 정보 추가
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "로컬 개발 서버",
        },
        {
            "url": "https://api.example.com",
            "description": "운영 서버 (예시)",
        },
    ]

    # 커스텀 메타데이터 추가
    openapi_schema["info"]["x-api-status"] = "학습용 프로젝트"
    openapi_schema["info"]["x-last-updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 스키마를 캐시에 저장
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# FastAPI의 openapi 메서드를 커스텀 함수로 교체
app.openapi = custom_openapi
