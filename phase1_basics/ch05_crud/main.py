"""
Chapter 05 - 메모리 기반 CRUD API
=================================
이 모듈에서는 인메모리 딕셔너리를 사용하여 완전한 CRUD API를 구현한다:
- POST /items/          → 아이템 생성 (Create)
- GET /items/           → 아이템 목록 조회 (Read - List)
- GET /items/{item_id}  → 아이템 단건 조회 (Read - Detail)
- PUT /items/{item_id}  → 아이템 수정 (Update)
- DELETE /items/{item_id} → 아이템 삭제 (Delete)

실행 방법:
    uvicorn main:app --reload
"""

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from datetime import datetime

app = FastAPI(
    title="Chapter 05 - 메모리 기반 CRUD API",
    description="인메모리 딕셔너리를 사용한 RESTful CRUD API 학습",
    version="1.0.0",
)

# ============================================================
# Pydantic 모델 정의
# ============================================================
# 실무에서는 요청/응답 모델을 분리하는 것이 원칙이다.
# - Create 모델: 생성 시 클라이언트가 보내는 데이터
# - Update 모델: 수정 시 클라이언트가 보내는 데이터 (필드가 선택적일 수 있음)
# - Response 모델: 서버가 클라이언트에게 반환하는 데이터
# ============================================================


class ItemCreate(BaseModel):
    """
    아이템 생성 요청 모델.
    클라이언트가 POST 요청 시 보내는 데이터 구조를 정의한다.
    id와 created_at은 서버에서 자동 생성하므로 포함하지 않는다.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["무선 키보드"],
        description="아이템 이름",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        examples=["블루투스 기계식 키보드"],
        description="아이템 설명 (선택)",
    )
    price: float = Field(
        ...,
        gt=0,
        examples=[59000],
        description="아이템 가격 (0보다 커야 함)",
    )
    is_available: bool = Field(
        default=True,
        description="판매 가능 여부",
    )


class ItemUpdate(BaseModel):
    """
    아이템 수정 요청 모델.
    PUT 요청에서 사용하며, 모든 필드를 선택적(Optional)으로 정의한다.
    클라이언트는 변경하고 싶은 필드만 보낼 수 있다.
    """
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        examples=["무선 키보드 (개선판)"],
        description="아이템 이름",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        examples=["신형 블루투스 기계식 키보드"],
        description="아이템 설명",
    )
    price: float | None = Field(
        default=None,
        gt=0,
        examples=[65000],
        description="아이템 가격",
    )
    is_available: bool | None = Field(
        default=None,
        description="판매 가능 여부",
    )


class ItemResponse(BaseModel):
    """
    아이템 응답 모델.
    서버가 클라이언트에게 반환하는 데이터 구조를 정의한다.
    id, created_at, updated_at 등 서버에서 관리하는 필드가 포함된다.
    """
    id: int
    name: str
    description: str | None = None
    price: float
    is_available: bool
    created_at: datetime
    updated_at: datetime


class ItemListResponse(BaseModel):
    """
    아이템 목록 응답 모델.
    페이지네이션 정보와 함께 아이템 목록을 반환한다.
    """
    total: int = Field(description="전체 아이템 수")
    skip: int = Field(description="건너뛴 아이템 수")
    limit: int = Field(description="요청한 최대 아이템 수")
    items: list[ItemResponse] = Field(description="아이템 목록")


# ============================================================
# 인메모리 저장소
# ============================================================
# 실제 프로젝트에서는 데이터베이스를 사용하지만,
# 학습 목적으로 파이썬 딕셔너리를 저장소로 활용한다.
# 서버가 재시작되면 모든 데이터가 초기화된다.
# ============================================================

items_db: dict[int, dict] = {}
item_id_counter: int = 0


# ============================================================
# CREATE - POST /items/
# ============================================================


@app.post(
    "/items/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="아이템 생성",
    tags=["아이템 CRUD"],
)
def create_item(item: ItemCreate):
    """
    새로운 아이템을 생성한다.

    **REST 규칙**:
    - HTTP 메서드: **POST** (새 리소스 생성)
    - URL: 컬렉션 경로 `/items/` (특정 ID 없음)
    - 상태 코드: **201 Created** (리소스 생성 성공)
    - 응답 본문: 생성된 리소스의 전체 정보 (서버가 부여한 id 포함)
    """
    global item_id_counter
    item_id_counter += 1

    now = datetime.now()

    # 새 아이템 데이터를 구성한다
    item_data = {
        "id": item_id_counter,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "is_available": item.is_available,
        "created_at": now,
        "updated_at": now,
    }

    # 인메모리 저장소에 저장한다
    items_db[item_id_counter] = item_data

    return item_data


# ============================================================
# READ (List) - GET /items/
# ============================================================


@app.get(
    "/items/",
    response_model=ItemListResponse,
    summary="아이템 목록 조회 (페이지네이션)",
    tags=["아이템 CRUD"],
)
def list_items(
    skip: int = Query(
        default=0,
        ge=0,
        description="건너뛸 아이템 수 (오프셋)",
        examples=[0],
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="한 번에 조회할 최대 아이템 수 (1~100)",
        examples=[10],
    ),
):
    """
    아이템 목록을 페이지네이션하여 조회한다.

    **REST 규칙**:
    - HTTP 메서드: **GET** (리소스 조회, 서버 상태를 변경하지 않음)
    - URL: 컬렉션 경로 `/items/`
    - 쿼리 파라미터: `skip`(오프셋)과 `limit`(페이지 크기)로 페이지네이션

    **페이지네이션 예시**:
    - `?skip=0&limit=10` → 1~10번째 아이템
    - `?skip=10&limit=10` → 11~20번째 아이템
    - `?skip=20&limit=5` → 21~25번째 아이템
    """
    # 전체 아이템 목록을 리스트로 변환한다
    all_items = list(items_db.values())

    # skip과 limit을 적용하여 페이지네이션한다
    # 파이썬 슬라이싱: list[skip : skip + limit]
    paginated_items = all_items[skip: skip + limit]

    return ItemListResponse(
        total=len(all_items),
        skip=skip,
        limit=limit,
        items=paginated_items,
    )


# ============================================================
# READ (Detail) - GET /items/{item_id}
# ============================================================


@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    responses={
        404: {
            "description": "아이템을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {"detail": "아이템 ID 999를 찾을 수 없습니다"}
                }
            },
        },
    },
    summary="아이템 단건 조회",
    tags=["아이템 CRUD"],
)
def get_item(item_id: int):
    """
    특정 아이템을 ID로 조회한다.

    **REST 규칙**:
    - HTTP 메서드: **GET**
    - URL: 개별 리소스 경로 `/items/{item_id}` (특정 ID 지정)
    - 존재하지 않는 ID로 요청하면 **404 Not Found**를 반환한다
    """
    # 저장소에서 아이템을 검색한다
    if item_id not in items_db:
        # HTTPException을 발생시켜 적절한 에러 응답을 반환한다
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아이템 ID {item_id}를 찾을 수 없습니다",
        )

    return items_db[item_id]


# ============================================================
# UPDATE - PUT /items/{item_id}
# ============================================================


@app.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    responses={
        404: {
            "description": "아이템을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {"detail": "아이템 ID 999를 찾을 수 없습니다"}
                }
            },
        },
    },
    summary="아이템 수정",
    tags=["아이템 CRUD"],
)
def update_item(item_id: int, item_update: ItemUpdate):
    """
    특정 아이템을 수정한다.

    **REST 규칙**:
    - HTTP 메서드: **PUT** (리소스 수정)
    - URL: 개별 리소스 경로 `/items/{item_id}`
    - 요청 본문: 수정할 필드만 포함 (나머지 필드는 기존 값 유지)
    - 존재하지 않는 ID로 요청하면 **404 Not Found**를 반환한다

    **참고**: 엄밀한 REST에서 PUT은 전체 교체, PATCH는 부분 수정이지만,
    이 예제에서는 편의상 PUT으로 부분 수정을 허용한다.
    """
    # 아이템 존재 여부를 먼저 확인한다
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아이템 ID {item_id}를 찾을 수 없습니다",
        )

    # 기존 아이템 데이터를 가져온다
    existing_item = items_db[item_id]

    # model_dump(exclude_unset=True)로 클라이언트가 실제로 보낸 필드만 추출한다
    # exclude_unset=True: 기본값이 아닌, 명시적으로 설정된 필드만 포함
    # 예: {"name": "새이름"}만 보냈다면 name만 포함, price/description은 제외
    update_data = item_update.model_dump(exclude_unset=True)

    # 기존 데이터에 변경 사항을 덮어쓴다
    for field, value in update_data.items():
        existing_item[field] = value

    # 수정 시각을 갱신한다
    existing_item["updated_at"] = datetime.now()

    # 저장소에 반영한다
    items_db[item_id] = existing_item

    return existing_item


# ============================================================
# DELETE - DELETE /items/{item_id}
# ============================================================


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {
            "description": "아이템을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {"detail": "아이템 ID 999를 찾을 수 없습니다"}
                }
            },
        },
    },
    summary="아이템 삭제",
    tags=["아이템 CRUD"],
)
def delete_item(item_id: int):
    """
    특정 아이템을 삭제한다.

    **REST 규칙**:
    - HTTP 메서드: **DELETE** (리소스 삭제)
    - URL: 개별 리소스 경로 `/items/{item_id}`
    - 상태 코드: **204 No Content** (삭제 성공, 응답 본문 없음)
    - 존재하지 않는 ID로 요청하면 **404 Not Found**를 반환한다

    **204 상태 코드**: 요청이 성공했지만 응답 본문에 전달할 내용이 없음을 의미한다.
    삭제된 리소스를 다시 반환할 필요가 없으므로 204가 적절하다.
    """
    # 아이템 존재 여부를 확인한다
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아이템 ID {item_id}를 찾을 수 없습니다",
        )

    # 저장소에서 아이템을 제거한다
    del items_db[item_id]

    # 204 응답은 본문이 없으므로 None을 반환한다
    return None
