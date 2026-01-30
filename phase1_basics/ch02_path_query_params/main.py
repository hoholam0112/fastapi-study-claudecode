"""
Chapter 02 - Path 파라미터와 Query 파라미터
==========================================
경로 매개변수, 쿼리 매개변수, Enum을 활용한 API 설계 예제.
타입 힌트 기반의 자동 검증 기능을 확인한다.
"""

from enum import Enum
from typing import Optional

from fastapi import FastAPI, Query, Path

# ============================================================
# FastAPI 앱 인스턴스 생성
# ============================================================
app = FastAPI(
    title="Chapter 02 - Path & Query 파라미터",
    description="Path 파라미터, Query 파라미터, Enum 활용 예제 API",
    version="1.0.0",
)


# ============================================================
# Enum 클래스 정의 - 카테고리 필터링에 사용
# ============================================================
# str과 Enum을 동시에 상속하면 JSON 직렬화와 Swagger UI에서 문자열로 처리된다.
# Swagger UI에서는 드롭다운 선택지로 자동 표시된다.
class CategoryName(str, Enum):
    electronics = "electronics"  # 전자기기
    books = "books"              # 도서
    clothing = "clothing"        # 의류
    food = "food"                # 식품


# ============================================================
# 정렬 순서를 위한 Enum 클래스
# ============================================================
class SortOrder(str, Enum):
    asc = "asc"    # 오름차순
    desc = "desc"  # 내림차순


# ============================================================
# 예시 데이터 (실제로는 데이터베이스에서 조회)
# ============================================================
# 학습용 더미 데이터. 실무에서는 DB에서 가져온다.
FAKE_ITEMS_DB = [
    {"item_id": 1, "name": "노트북", "category": "electronics", "price": 1200000, "in_stock": True},
    {"item_id": 2, "name": "파이썬 완벽 가이드", "category": "books", "price": 35000, "in_stock": True},
    {"item_id": 3, "name": "겨울 패딩", "category": "clothing", "price": 89000, "in_stock": False},
    {"item_id": 4, "name": "무선 이어폰", "category": "electronics", "price": 250000, "in_stock": True},
    {"item_id": 5, "name": "FastAPI 입문", "category": "books", "price": 28000, "in_stock": True},
    {"item_id": 6, "name": "유기농 사과", "category": "food", "price": 15000, "in_stock": True},
    {"item_id": 7, "name": "기계식 키보드", "category": "electronics", "price": 150000, "in_stock": False},
    {"item_id": 8, "name": "면 티셔츠", "category": "clothing", "price": 25000, "in_stock": True},
]


# ============================================================
# 1. 기본 Path 파라미터
# ============================================================
# {item_id}는 URL 경로의 일부로 전달된다.
# int 타입 힌트를 지정하면 FastAPI가 자동으로 정수 변환 및 검증을 수행한다.
# 문자열이 정수로 변환되지 않으면 422 에러가 자동 반환된다.
@app.get(
    "/items/{item_id}",
    summary="단일 아이템 조회",
    description="item_id(정수)에 해당하는 아이템을 반환한다.",
    tags=["아이템"],
)
def read_item(
    item_id: int = Path(
        ...,
        title="아이템 ID",
        description="조회할 아이템의 고유 식별자 (1 이상의 정수)",
        ge=1,  # ge: greater than or equal (1 이상)
        examples=[1, 2, 3],
    ),
):
    """
    Path 파라미터로 전달된 item_id에 해당하는 아이템을 조회한다.

    - **item_id**: 1 이상의 정수 (Path 파라미터)
    """
    # 더미 데이터에서 해당 ID의 아이템을 검색한다.
    for item in FAKE_ITEMS_DB:
        if item["item_id"] == item_id:
            return item
    # 해당 ID의 아이템이 없으면 메시지를 반환한다.
    return {"message": f"item_id={item_id}에 해당하는 아이템을 찾을 수 없습니다."}


# ============================================================
# 2. Query 파라미터 (기본값 포함)
# ============================================================
# 함수 매개변수 중 Path에 포함되지 않은 것은 자동으로 Query 파라미터로 처리된다.
# 기본값이 있으면 선택적(optional) 파라미터, 없으면 필수(required) 파라미터이다.
@app.get(
    "/items/",
    summary="아이템 목록 조회 (페이지네이션)",
    description="skip과 limit을 사용한 페이지네이션으로 아이템 목록을 조회한다.",
    tags=["아이템"],
)
def read_items(
    skip: int = Query(
        default=0,
        title="건너뛸 개수",
        description="목록에서 처음 N개를 건너뛴다 (페이지네이션용)",
        ge=0,  # 0 이상
    ),
    limit: int = Query(
        default=10,
        title="조회 개수",
        description="한 번에 조회할 최대 아이템 수",
        ge=1,   # 최소 1개
        le=100,  # 최대 100개
    ),
):
    """
    전체 아이템 목록에서 skip만큼 건너뛰고 limit만큼 반환한다.

    - **skip**: 건너뛸 개수 (기본값: 0)
    - **limit**: 조회할 최대 개수 (기본값: 10, 최대: 100)
    """
    return {
        "total": len(FAKE_ITEMS_DB),
        "skip": skip,
        "limit": limit,
        "items": FAKE_ITEMS_DB[skip : skip + limit],
    }


# ============================================================
# 3. Path 파라미터 + Optional Query 파라미터 조합
# ============================================================
# Optional[str]로 선언하고 기본값을 None으로 설정하면 선택적 파라미터가 된다.
# 클라이언트가 값을 보내지 않으면 None이 할당된다.
@app.get(
    "/items/{item_id}/details",
    summary="아이템 상세 조회",
    description="아이템 ID로 조회하되, 선택적으로 검색어(q)를 추가할 수 있다.",
    tags=["아이템"],
)
def read_item_detail(
    item_id: int = Path(..., title="아이템 ID", ge=1),
    q: Optional[str] = Query(
        default=None,
        title="검색어",
        description="추가 검색 키워드 (선택)",
        min_length=1,
        max_length=50,
    ),
    include_description: bool = Query(
        default=False,
        title="설명 포함 여부",
        description="True로 설정하면 상세 설명을 포함한다",
    ),
):
    """
    Path 파라미터와 Query 파라미터를 조합하여 아이템을 조회한다.

    - **item_id**: 아이템 ID (Path 파라미터, 필수)
    - **q**: 검색어 (Query 파라미터, 선택)
    - **include_description**: 상세 설명 포함 여부 (Query 파라미터, 기본값: false)
    """
    # 해당 ID의 아이템을 검색한다.
    result = None
    for item in FAKE_ITEMS_DB:
        if item["item_id"] == item_id:
            result = dict(item)  # 원본을 수정하지 않기 위해 복사
            break

    if result is None:
        return {"message": f"item_id={item_id}에 해당하는 아이템이 없습니다."}

    # 선택적 검색어가 있으면 응답에 포함한다.
    if q:
        result["search_query"] = q

    # include_description이 True이면 설명을 추가한다.
    # bool 타입은 true, yes, on, 1 등의 값을 모두 True로 인식한다.
    if include_description:
        result["description"] = f"{result['name']}에 대한 상세 설명입니다."

    return result


# ============================================================
# 4. Enum을 활용한 카테고리 필터링
# ============================================================
# CategoryName Enum을 Path 파라미터로 사용하면,
# 정의된 값(electronics, books, clothing, food)만 허용된다.
# Swagger UI에서는 드롭다운 선택지로 표시된다.
@app.get(
    "/categories/{category_name}",
    summary="카테고리별 아이템 조회",
    description="Enum으로 정의된 카테고리에 해당하는 아이템들을 반환한다.",
    tags=["카테고리"],
)
def get_category_items(
    category_name: CategoryName = Path(
        ...,
        title="카테고리명",
        description="조회할 카테고리 (electronics, books, clothing, food)",
    ),
):
    """
    지정한 카테고리에 속하는 아이템 목록을 반환한다.

    - **category_name**: 카테고리 이름 (Enum으로 제한)

    허용되지 않는 카테고리 값을 입력하면 422 에러가 자동 반환된다.
    """
    # Enum의 value 속성으로 실제 문자열 값에 접근한다.
    filtered = [
        item for item in FAKE_ITEMS_DB
        if item["category"] == category_name.value
    ]
    return {
        "category": category_name.value,
        "count": len(filtered),
        "items": filtered,
    }


# ============================================================
# 5. 복합 조합 - Path + 여러 Query 파라미터
# ============================================================
# 실무에서 자주 사용하는 패턴: Path로 리소스를 특정하고,
# Query로 필터링/정렬/페이지네이션을 처리한다.
@app.get(
    "/products/{product_id}",
    summary="상품 상세 조회 (복합 파라미터)",
    description="Path, Query, Enum, Optional, bool 파라미터를 모두 조합한 예제이다.",
    tags=["상품"],
)
def get_product(
    product_id: int = Path(
        ...,
        title="상품 ID",
        description="조회할 상품의 고유 ID",
        ge=1,
    ),
    category: Optional[CategoryName] = Query(
        default=None,
        title="카테고리 필터",
        description="특정 카테고리로 필터링 (선택)",
    ),
    in_stock: Optional[bool] = Query(
        default=None,
        title="재고 여부",
        description="True: 재고 있음만, False: 품절만, 미지정: 전체",
    ),
    min_price: Optional[int] = Query(
        default=None,
        title="최소 가격",
        description="이 가격 이상인 상품만 조회",
        ge=0,
    ),
    max_price: Optional[int] = Query(
        default=None,
        title="최대 가격",
        description="이 가격 이하인 상품만 조회",
        ge=0,
    ),
):
    """
    다양한 파라미터를 조합하여 상품을 조회한다.

    - **product_id**: 상품 ID (Path, 필수)
    - **category**: 카테고리 필터 (Query, 선택, Enum)
    - **in_stock**: 재고 필터 (Query, 선택, bool)
    - **min_price**: 최소 가격 (Query, 선택)
    - **max_price**: 최대 가격 (Query, 선택)
    """
    # 상품 ID로 먼저 조회한다.
    product = None
    for item in FAKE_ITEMS_DB:
        if item["item_id"] == product_id:
            product = dict(item)
            break

    if product is None:
        return {"message": f"product_id={product_id}에 해당하는 상품이 없습니다."}

    # 적용된 필터 정보를 함께 반환한다.
    filters_applied = {}

    # 카테고리 필터 적용
    if category is not None:
        filters_applied["category"] = category.value
        if product["category"] != category.value:
            return {
                "message": "해당 상품은 지정한 카테고리에 속하지 않습니다.",
                "product_category": product["category"],
                "filter_category": category.value,
            }

    # 재고 필터 적용
    if in_stock is not None:
        filters_applied["in_stock"] = in_stock
        if product["in_stock"] != in_stock:
            stock_status = "재고 있음" if product["in_stock"] else "품절"
            return {
                "message": f"해당 상품은 현재 '{stock_status}' 상태입니다.",
                "filter_in_stock": in_stock,
            }

    # 가격 범위 필터 적용
    if min_price is not None:
        filters_applied["min_price"] = min_price
    if max_price is not None:
        filters_applied["max_price"] = max_price

    if min_price is not None and product["price"] < min_price:
        return {"message": "해당 상품의 가격이 최소 가격 조건보다 낮습니다."}
    if max_price is not None and product["price"] > max_price:
        return {"message": "해당 상품의 가격이 최대 가격 조건보다 높습니다."}

    # 최종 결과 반환
    product["filters_applied"] = filters_applied
    return product


# ============================================================
# 6. 아이템 검색 - Query 파라미터만 사용하는 패턴
# ============================================================
# Path 파라미터 없이 Query 파라미터만으로 필터링/검색하는 예제.
@app.get(
    "/search/",
    summary="아이템 검색",
    description="카테고리, 가격, 재고 등 다양한 조건으로 아이템을 검색한다.",
    tags=["검색"],
)
def search_items(
    keyword: Optional[str] = Query(
        default=None,
        title="검색 키워드",
        description="아이템 이름에 포함된 키워드로 검색",
        min_length=1,
        max_length=100,
    ),
    category: Optional[CategoryName] = Query(
        default=None,
        title="카테고리",
        description="특정 카테고리로 필터링",
    ),
    sort_by_price: Optional[SortOrder] = Query(
        default=None,
        title="가격 정렬",
        description="가격 기준 오름차순(asc) 또는 내림차순(desc) 정렬",
    ),
    in_stock_only: bool = Query(
        default=False,
        title="재고 있는 상품만",
        description="True: 재고 있는 상품만 표시",
    ),
    skip: int = Query(default=0, ge=0, title="건너뛸 개수"),
    limit: int = Query(default=10, ge=1, le=100, title="조회 개수"),
):
    """
    다양한 Query 파라미터를 조합하여 아이템을 검색한다.

    - **keyword**: 이름 검색어 (선택)
    - **category**: 카테고리 필터 (선택, Enum)
    - **sort_by_price**: 가격 정렬 순서 (선택, Enum)
    - **in_stock_only**: 재고 있는 상품만 표시 (기본값: false)
    - **skip**, **limit**: 페이지네이션
    """
    results = list(FAKE_ITEMS_DB)

    # 키워드 필터링 - 아이템 이름에 키워드가 포함되어 있는지 확인
    if keyword:
        results = [item for item in results if keyword in item["name"]]

    # 카테고리 필터링
    if category:
        results = [item for item in results if item["category"] == category.value]

    # 재고 필터링
    if in_stock_only:
        results = [item for item in results if item["in_stock"]]

    # 가격 정렬
    if sort_by_price:
        reverse = sort_by_price == SortOrder.desc
        results.sort(key=lambda x: x["price"], reverse=reverse)

    # 전체 결과 수 (페이지네이션 적용 전)
    total = len(results)

    # 페이지네이션 적용
    results = results[skip : skip + limit]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": results,
    }


# ============================================================
# 직접 실행 시 uvicorn으로 서버를 시작한다.
# ============================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
