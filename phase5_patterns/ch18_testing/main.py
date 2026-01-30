"""
Chapter 18: FastAPI 테스트 - 메인 애플리케이션

간단한 아이템 CRUD API를 제공하는 FastAPI 애플리케이션.
인메모리 딕셔너리를 데이터 저장소로 사용한다.
테스트 가능한 구조로 설계되어 있으며,
의존성 주입을 통해 데이터 저장소를 교체할 수 있다.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field

# ============================================================
# FastAPI 앱 인스턴스 생성
# ============================================================
app = FastAPI(
    title="아이템 관리 API",
    description="테스트 학습을 위한 간단한 아이템 CRUD API",
    version="1.0.0",
)

# ============================================================
# 인메모리 데이터 저장소
# 실제 프로젝트에서는 데이터베이스를 사용하지만,
# 테스트 학습 목적으로 딕셔너리를 사용한다.
# ============================================================
fake_db: dict[int, dict] = {}

# 아이템 ID를 자동 증가시키기 위한 카운터
_id_counter: dict[str, int] = {"current": 0}


def _next_id() -> int:
    """다음 아이템 ID를 생성하는 내부 헬퍼 함수"""
    _id_counter["current"] += 1
    return _id_counter["current"]


# ============================================================
# Pydantic 모델 정의
# 요청/응답 데이터의 유효성 검증과 직렬화를 담당한다.
# ============================================================
class ItemCreate(BaseModel):
    """아이템 생성 시 클라이언트가 보내는 데이터"""

    name: str = Field(..., min_length=1, max_length=100, description="아이템 이름")
    description: str | None = Field(None, max_length=500, description="아이템 설명")
    price: float = Field(..., gt=0, description="아이템 가격 (0보다 커야 함)")


class ItemResponse(BaseModel):
    """아이템 응답 데이터"""

    id: int = Field(..., description="아이템 고유 ID")
    name: str = Field(..., description="아이템 이름")
    description: str | None = Field(None, description="아이템 설명")
    price: float = Field(..., description="아이템 가격")


# ============================================================
# 의존성 함수
# 테스트 시 dependency_overrides로 교체할 수 있도록
# 데이터 저장소 접근을 의존성으로 분리한다.
# ============================================================
def get_db() -> dict[int, dict]:
    """
    데이터 저장소(인메모리 딕셔너리)를 반환하는 의존성 함수.

    테스트 환경에서는 이 의존성을 오버라이드하여
    테스트 전용 데이터 저장소를 주입할 수 있다.
    """
    return fake_db


# ============================================================
# API 엔드포인트 정의
# ============================================================
@app.post(
    "/items/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새 아이템 생성",
)
def create_item(item: ItemCreate, db: dict = Depends(get_db)):
    """
    새로운 아이템을 생성한다.

    - **name**: 아이템 이름 (필수)
    - **description**: 아이템 설명 (선택)
    - **price**: 아이템 가격 (필수, 0보다 커야 함)
    """
    item_id = _next_id()
    db[item_id] = {
        "id": item_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
    }
    return db[item_id]


@app.get(
    "/items/",
    response_model=list[ItemResponse],
    summary="전체 아이템 목록 조회",
)
def read_items(db: dict = Depends(get_db)):
    """저장된 모든 아이템 목록을 반환한다."""
    return list(db.values())


@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="특정 아이템 조회",
)
def read_item(item_id: int, db: dict = Depends(get_db)):
    """
    ID로 특정 아이템을 조회한다.

    해당 ID의 아이템이 존재하지 않으면 404 에러를 반환한다.
    """
    if item_id not in db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아이템 ID {item_id}을(를) 찾을 수 없습니다",
        )
    return db[item_id]


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_200_OK,
    summary="아이템 삭제",
)
def delete_item(item_id: int, db: dict = Depends(get_db)):
    """
    ID로 특정 아이템을 삭제한다.

    해당 ID의 아이템이 존재하지 않으면 404 에러를 반환한다.
    삭제 성공 시 확인 메시지를 반환한다.
    """
    if item_id not in db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아이템 ID {item_id}을(를) 찾을 수 없습니다",
        )
    deleted_item = db.pop(item_id)
    return {"message": f"아이템 '{deleted_item['name']}'이(가) 삭제되었습니다"}
