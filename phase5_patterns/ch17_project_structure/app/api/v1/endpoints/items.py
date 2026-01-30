"""
아이템 API 엔드포인트 모듈

아이템 리소스에 대한 CRUD 엔드포인트를 정의한다.
사용자 엔드포인트와 동일한 패턴을 따르며,
인메모리 저장소를 사용하여 데이터를 관리한다.

실습 포인트:
    이 모듈을 참고하여 별도의 schemas/item.py, crud/item.py를
    만들어 계층 분리를 직접 실습해 보자.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# ──────────────────────────────────────────────
# 아이템 스키마 (간단한 데모를 위해 같은 파일에 정의)
# 실제 프로젝트에서는 app/schemas/item.py로 분리한다
# ──────────────────────────────────────────────


class ItemCreate(BaseModel):
    """아이템 생성 요청 스키마"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="아이템 이름",
        examples=["노트북"],
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="아이템 설명 (선택사항)",
        examples=["업무용 고성능 노트북"],
    )
    price: float = Field(
        ...,
        gt=0,
        description="아이템 가격 (0보다 큰 값)",
        examples=[1500000.0],
    )


class ItemUpdate(BaseModel):
    """아이템 수정 요청 스키마"""

    name: str | None = Field(None, min_length=1, max_length=100, description="아이템 이름")
    description: str | None = Field(None, max_length=500, description="아이템 설명")
    price: float | None = Field(None, gt=0, description="아이템 가격")


class ItemResponse(BaseModel):
    """아이템 응답 스키마"""

    id: int = Field(..., description="아이템 고유 ID")
    name: str = Field(..., description="아이템 이름")
    description: str | None = Field(None, description="아이템 설명")
    price: float = Field(..., description="아이템 가격")


# ──────────────────────────────────────────────
# 인메모리 데이터 저장소 (데모용)
# 실제 프로젝트에서는 app/crud/item.py로 분리한다
# ──────────────────────────────────────────────

_items_db: dict[int, dict] = {}
_next_id: int = 1

# ──────────────────────────────────────────────
# 아이템 라우터 정의
# ──────────────────────────────────────────────

# 아이템 라우터 생성
# prefix: 모든 경로에 "/items" 접두사 추가
# tags: Swagger UI에서 "items" 그룹으로 표시
router = APIRouter(prefix="/items", tags=["items"])


@router.get(
    "/",
    response_model=list[ItemResponse],
    summary="전체 아이템 목록 조회",
    description="등록된 모든 아이템의 목록을 반환한다.",
)
async def get_items():
    """
    전체 아이템 목록을 조회하는 엔드포인트

    Returns:
        등록된 모든 아이템 리스트
    """
    return [ItemResponse(**item_data) for item_data in _items_db.values()]


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="아이템 생성",
    description="새로운 아이템을 생성하고, 생성된 아이템 정보를 반환한다.",
)
async def create_item(item_in: ItemCreate):
    """
    새로운 아이템을 생성하는 엔드포인트

    Args:
        item_in: 아이템 생성 요청 데이터 (name, description, price)

    Returns:
        생성된 아이템 정보
    """
    global _next_id

    # 새 아이템 데이터 구성
    item_data = {
        "id": _next_id,
        "name": item_in.name,
        "description": item_in.description,
        "price": item_in.price,
    }

    # 인메모리 저장소에 저장
    _items_db[_next_id] = item_data
    _next_id += 1

    return ItemResponse(**item_data)


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="특정 아이템 조회",
    description="ID를 기반으로 특정 아이템의 정보를 조회한다.",
)
async def get_item(item_id: int):
    """
    특정 아이템을 ID로 조회하는 엔드포인트

    Args:
        item_id: 조회할 아이템의 고유 ID

    Returns:
        해당 아이템 정보

    Raises:
        HTTPException(404): 아이템을 찾을 수 없는 경우
    """
    item_data = _items_db.get(item_id)
    if item_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {item_id}에 해당하는 아이템을 찾을 수 없습니다.",
        )
    return ItemResponse(**item_data)


@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    summary="아이템 정보 수정",
    description="기존 아이템의 정보를 수정한다. 전달된 필드만 업데이트된다.",
)
async def update_item(item_id: int, item_in: ItemUpdate):
    """
    아이템 정보를 수정하는 엔드포인트

    Args:
        item_id: 수정할 아이템의 고유 ID
        item_in: 수정할 데이터 (변경할 필드만 전송 가능)

    Returns:
        수정된 아이템 정보

    Raises:
        HTTPException(404): 아이템을 찾을 수 없는 경우
    """
    if item_id not in _items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {item_id}에 해당하는 아이템을 찾을 수 없습니다.",
        )

    # 기존 데이터를 가져와서 전달된 필드만 업데이트한다
    stored_data = _items_db[item_id]
    update_data = item_in.model_dump(exclude_unset=True)
    stored_data.update(update_data)
    _items_db[item_id] = stored_data

    return ItemResponse(**stored_data)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="아이템 삭제",
    description="ID를 기반으로 아이템을 삭제한다.",
)
async def delete_item(item_id: int):
    """
    아이템을 삭제하는 엔드포인트

    Args:
        item_id: 삭제할 아이템의 고유 ID

    Raises:
        HTTPException(404): 아이템을 찾을 수 없는 경우
    """
    if item_id not in _items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {item_id}에 해당하는 아이템을 찾을 수 없습니다.",
        )

    del _items_db[item_id]
    # 204 응답은 본문(body)을 반환하지 않는다
    return None
