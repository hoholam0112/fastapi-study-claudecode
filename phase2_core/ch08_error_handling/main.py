"""
Chapter 08: 에러 처리 (Error Handling)

HTTPException, 커스텀 예외 클래스, 전역 예외 핸들러,
RequestValidationError 오버라이드, 통일된 에러 응답 포맷을 학습한다.

실행 방법:
    uvicorn main:app --reload
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ============================================================
# 로거 설정
# - 에러 발생 시 서버 로그에 기록하기 위한 설정
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ch08_error_handling")


# ============================================================
# 통일된 에러 응답 모델
# - 모든 에러 응답이 동일한 구조를 따르도록 설계
# - 클라이언트에서 에러를 일관되게 처리할 수 있음
# ============================================================
class ErrorDetail(BaseModel):
    """에러 상세 정보 모델."""
    code: str = Field(..., description="에러 코드 (영문 대문자 + 밑줄)")
    message: str = Field(..., description="사용자에게 보여줄 에러 메시지")
    detail: Optional[Any] = Field(None, description="추가 상세 정보")


class ErrorResponse(BaseModel):
    """
    통일된 에러 응답 모델.
    모든 에러 응답은 이 형식을 따른다.
    """
    success: bool = Field(False, description="요청 성공 여부 (항상 False)")
    error: ErrorDetail = Field(..., description="에러 상세 정보")
    timestamp: str = Field(..., description="에러 발생 시각 (ISO 8601)")
    path: Optional[str] = Field(None, description="에러가 발생한 요청 경로")


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    detail: Any = None,
    path: Optional[str] = None,
) -> JSONResponse:
    """
    통일된 에러 응답을 생성하는 헬퍼 함수.
    모든 예외 핸들러에서 이 함수를 사용하여 일관된 응답을 반환한다.
    """
    content = ErrorResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, detail=detail),
        timestamp=datetime.now(timezone.utc).isoformat(),
        path=path,
    ).model_dump()

    return JSONResponse(status_code=status_code, content=content)


# ============================================================
# 커스텀 예외 클래스 정의
# - 비즈니스 로직에 특화된 예외 계층 구조
# - 각 예외는 고유한 에러 코드와 메시지를 가짐
# ============================================================
class AppException(Exception):
    """
    애플리케이션 기본 예외 클래스.
    모든 커스텀 예외의 부모 클래스로, 공통 속성을 정의한다.
    """

    def __init__(
        self,
        code: str = "APP_ERROR",
        message: str = "애플리케이션 에러가 발생했습니다",
        status_code: int = 500,
        detail: Any = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class ItemNotFoundException(AppException):
    """아이템을 찾을 수 없을 때 발생하는 예외."""

    def __init__(self, item_id: int):
        super().__init__(
            code="ITEM_NOT_FOUND",
            message=f"아이템 ID {item_id}을(를) 찾을 수 없습니다",
            status_code=404,
            detail={"item_id": item_id},
        )


class InsufficientStockException(AppException):
    """재고가 부족할 때 발생하는 예외."""

    def __init__(self, item_id: int, requested: int, available: int):
        super().__init__(
            code="INSUFFICIENT_STOCK",
            message=f"재고가 부족합니다. 요청: {requested}개, 재고: {available}개",
            status_code=409,
            detail={
                "item_id": item_id,
                "requested": requested,
                "available": available,
            },
        )


class PermissionDeniedException(AppException):
    """권한이 부족할 때 발생하는 예외."""

    def __init__(self, action: str):
        super().__init__(
            code="PERMISSION_DENIED",
            message=f"'{action}' 작업에 대한 권한이 없습니다",
            status_code=403,
            detail={"action": action},
        )


# ============================================================
# FastAPI 앱 생성
# ============================================================
app = FastAPI(
    title="Chapter 08: 에러 처리",
    description="HTTPException, 커스텀 예외, 전역 핸들러, 에러 응답 통일 학습",
    version="1.0.0",
)


# ============================================================
# 전역 예외 핸들러 등록
# - 각 예외 타입에 대해 통일된 에러 응답을 반환
# - 핸들러 등록 순서는 중요하지 않음 (예외 타입으로 매칭)
# ============================================================
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    AppException 및 모든 하위 예외를 처리하는 핸들러.
    ItemNotFoundException, InsufficientStockException 등
    모든 커스텀 예외가 이 핸들러를 통해 처리된다.
    """
    logger.warning(
        f"[AppException] {exc.code}: {exc.message} | 경로: {request.url.path}"
    )
    return create_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        detail=exc.detail,
        path=str(request.url),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Pydantic 유효성 검증 실패 시 호출되는 핸들러.
    기본 422 응답 형식을 오버라이드하여 통일된 에러 포맷으로 반환한다.

    기본 FastAPI 응답:
        {"detail": [{"loc": [...], "msg": "...", "type": "..."}]}

    커스터마이징된 응답:
        {"success": false, "error": {"code": "VALIDATION_ERROR", ...}}
    """
    # 검증 에러의 상세 내용을 가독성 좋게 변환
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        f"[ValidationError] 경로: {request.url.path} | 에러 수: {len(error_details)}"
    )

    return create_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="요청 데이터의 유효성 검증에 실패했습니다",
        detail=error_details,
        path=str(request.url),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    FastAPI의 HTTPException을 처리하는 핸들러.
    기본 HTTPException 응답도 통일된 에러 포맷으로 변환한다.
    """
    # HTTP 상태 코드별 에러 코드 매핑
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
    }
    error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

    logger.warning(
        f"[HTTPException] {exc.status_code}: {exc.detail} | 경로: {request.url.path}"
    )

    response = create_error_response(
        status_code=exc.status_code,
        code=error_code,
        message=str(exc.detail),
        path=str(request.url),
    )

    # HTTPException에 커스텀 헤더가 있으면 응답에 추가
    if exc.headers:
        for key, value in exc.headers.items():
            response.headers[key] = value

    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    처리되지 않은 모든 예외를 잡는 최종 안전망.
    예상치 못한 에러가 발생해도 클라이언트에 일관된 응답을 반환한다.
    내부 에러 메시지는 로그에만 기록하고, 클라이언트에는 일반적인 메시지만 전달한다.
    """
    logger.error(
        f"[UnhandledException] {type(exc).__name__}: {str(exc)} | 경로: {request.url.path}",
        exc_info=True,  # 스택 트레이스도 로그에 기록
    )
    return create_error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="서버 내부 에러가 발생했습니다. 잠시 후 다시 시도해 주세요.",
        path=str(request.url),
    )


# ============================================================
# 더미 데이터 및 요청/응답 모델
# ============================================================
fake_items_db = {
    1: {"id": 1, "name": "노트북", "price": 1500000, "stock": 10},
    2: {"id": 2, "name": "키보드", "price": 150000, "stock": 25},
    3: {"id": 3, "name": "마우스", "price": 80000, "stock": 50},
}


class ItemCreate(BaseModel):
    """아이템 생성 요청 모델."""
    name: str = Field(..., min_length=1, max_length=100, description="아이템 이름")
    price: int = Field(..., gt=0, description="가격 (양수)")
    stock: int = Field(0, ge=0, description="재고 수량 (0 이상)")


class OrderCreate(BaseModel):
    """주문 생성 요청 모델."""
    item_id: int = Field(..., description="주문할 아이템 ID")
    quantity: int = Field(..., gt=0, description="주문 수량 (양수)")


# ============================================================
# 1. HTTPException 사용
# - 가장 기본적인 에러 반환 방법
# - status_code, detail, headers를 지정할 수 있음
# ============================================================
@app.get("/items/{item_id}", tags=["HTTPException"])
async def read_item(item_id: int):
    """
    아이템 조회.
    존재하지 않는 아이템 ID를 요청하면 HTTPException(404)이 발생한다.
    """
    item = fake_items_db.get(item_id)
    if item is None:
        # HTTPException: FastAPI의 기본 에러 반환 방법
        raise HTTPException(
            status_code=404,
            detail=f"아이템 ID {item_id}을(를) 찾을 수 없습니다",
        )
    return {"success": True, "data": item}


@app.get("/items/{item_id}/with-header", tags=["HTTPException"])
async def read_item_with_header(item_id: int):
    """
    아이템 조회 (커스텀 헤더 포함).
    에러 응답에 커스텀 HTTP 헤더를 추가하여 추가 정보를 전달할 수 있다.
    """
    item = fake_items_db.get(item_id)
    if item is None:
        # headers 매개변수로 응답 헤더에 추가 정보 포함
        raise HTTPException(
            status_code=404,
            detail=f"아이템 ID {item_id}을(를) 찾을 수 없습니다",
            headers={
                "X-Error-Code": "ITEM_NOT_FOUND",
                "X-Error-Item-Id": str(item_id),
            },
        )
    return {"success": True, "data": item}


# ============================================================
# 2. 커스텀 예외 클래스 사용
# - 비즈니스 로직에 맞는 예외를 정의하여 사용
# - 전역 핸들러(AppException)에서 자동으로 처리됨
# ============================================================
@app.get("/products/{product_id}", tags=["커스텀 예외"])
async def read_product(product_id: int):
    """
    상품 조회 (커스텀 예외 사용).
    ItemNotFoundException을 발생시키면 app_exception_handler에서 처리된다.
    """
    item = fake_items_db.get(product_id)
    if item is None:
        # 커스텀 예외 발생: AppException 핸들러가 통일된 형식으로 응답
        raise ItemNotFoundException(item_id=product_id)
    return {"success": True, "data": item}


@app.post("/orders/", tags=["커스텀 예외"])
async def create_order(order: OrderCreate):
    """
    주문 생성 (재고 부족 시 커스텀 예외 발생).

    비즈니스 로직:
    1. 아이템 존재 여부 확인 (ItemNotFoundException)
    2. 재고 수량 확인 (InsufficientStockException)
    3. 주문 생성
    """
    # 1단계: 아이템 존재 여부 확인
    item = fake_items_db.get(order.item_id)
    if item is None:
        raise ItemNotFoundException(item_id=order.item_id)

    # 2단계: 재고 확인
    if order.quantity > item["stock"]:
        raise InsufficientStockException(
            item_id=order.item_id,
            requested=order.quantity,
            available=item["stock"],
        )

    # 3단계: 주문 생성 (시뮬레이션)
    total_price = item["price"] * order.quantity
    return {
        "success": True,
        "data": {
            "order_id": 12345,
            "item": item["name"],
            "quantity": order.quantity,
            "total_price": total_price,
            "message": "주문이 성공적으로 생성되었습니다",
        },
    }


# ============================================================
# 3. RequestValidationError (유효성 검증 에러)
# - Pydantic 모델의 유효성 검증 실패 시 자동 발생
# - validation_exception_handler에서 통일된 형식으로 변환
# ============================================================
@app.post("/items/", tags=["유효성 검증 에러"])
async def create_item(item: ItemCreate):
    """
    아이템 생성.
    잘못된 데이터가 전달되면 RequestValidationError가 자동으로 발생한다.

    유효성 검증 조건:
    - name: 1~100자 문자열 (빈 문자열 불가)
    - price: 양수 정수 (0 이하 불가)
    - stock: 0 이상 정수
    """
    new_id = max(fake_items_db.keys()) + 1
    new_item = {"id": new_id, **item.model_dump()}
    fake_items_db[new_id] = new_item
    return {"success": True, "data": new_item}


# ============================================================
# 4. 엔드포인트 내 try/except 처리
# - 특정 에러를 엔드포인트 내에서 직접 처리
# - 복잡한 비즈니스 로직에서 단계별 에러 처리에 유용
# ============================================================
@app.get("/items/{item_id}/process", tags=["try/except"])
async def process_item(item_id: int):
    """
    아이템 처리 (try/except 사용).
    엔드포인트 내에서 여러 단계의 에러를 try/except로 직접 처리한다.
    """
    try:
        # 1단계: 아이템 조회
        item = fake_items_db.get(item_id)
        if item is None:
            raise ItemNotFoundException(item_id=item_id)

        # 2단계: 처리 로직 시뮬레이션
        if item["stock"] == 0:
            raise InsufficientStockException(
                item_id=item_id, requested=1, available=0
            )

        # 3단계: 결과 반환
        return {
            "success": True,
            "data": {
                "item": item,
                "processed": True,
                "message": f"'{item['name']}' 처리 완료",
            },
        }

    except AppException:
        # AppException 계열은 전역 핸들러에게 위임
        raise

    except Exception as e:
        # 예상치 못한 에러는 로깅 후 전역 핸들러에게 위임
        logger.error(f"아이템 처리 중 예상치 못한 에러: {e}")
        raise


# ============================================================
# 5. 권한 에러 및 다양한 에러 시나리오
# ============================================================
@app.delete("/items/{item_id}", tags=["권한 에러"])
async def delete_item(item_id: int):
    """
    아이템 삭제 (권한 에러 시연).
    현재는 인증 시스템이 없으므로 항상 권한 에러를 발생시킨다.
    """
    # 인증/인가 시스템이 없으므로 항상 권한 에러 발생 (시연용)
    raise PermissionDeniedException(action="아이템 삭제")


# ============================================================
# 6. 예상치 못한 에러 테스트
# - unhandled_exception_handler에서 처리됨
# - 내부 에러 메시지는 로그에만 기록
# ============================================================
@app.get("/error/unexpected", tags=["전역 에러 핸들러"])
async def trigger_unexpected_error():
    """
    예상치 못한 에러를 의도적으로 발생시키는 테스트 엔드포인트.
    unhandled_exception_handler가 이 에러를 잡아서 안전하게 처리한다.

    실제 운영 환경에서는 이런 에러가 발생하지 않도록 해야 하지만,
    만약의 경우를 대비한 안전망으로 전역 핸들러를 반드시 등록해야 한다.
    """
    # ZeroDivisionError: 처리되지 않은 예외
    result = 1 / 0
    return {"result": result}


@app.get("/error/value-error", tags=["전역 에러 핸들러"])
async def trigger_value_error():
    """
    ValueError를 발생시키는 테스트 엔드포인트.
    전역 핸들러가 모든 타입의 예외를 안전하게 처리하는지 확인한다.
    """
    raise ValueError("잘못된 값이 전달되었습니다")


# ============================================================
# 7. 에러 상태 확인 엔드포인트
# ============================================================
@app.get("/errors/catalog", tags=["에러 카탈로그"])
async def error_catalog():
    """
    이 API에서 발생할 수 있는 에러 코드 목록을 반환한다.
    클라이언트 개발자가 에러 처리 로직을 구현할 때 참고할 수 있다.
    """
    return {
        "success": True,
        "data": {
            "error_codes": [
                {
                    "code": "ITEM_NOT_FOUND",
                    "status": 404,
                    "description": "요청한 아이템이 존재하지 않음",
                },
                {
                    "code": "INSUFFICIENT_STOCK",
                    "status": 409,
                    "description": "재고가 주문 수량보다 부족함",
                },
                {
                    "code": "PERMISSION_DENIED",
                    "status": 403,
                    "description": "해당 작업에 대한 권한이 없음",
                },
                {
                    "code": "VALIDATION_ERROR",
                    "status": 422,
                    "description": "요청 데이터의 유효성 검증 실패",
                },
                {
                    "code": "NOT_FOUND",
                    "status": 404,
                    "description": "리소스를 찾을 수 없음 (일반)",
                },
                {
                    "code": "INTERNAL_SERVER_ERROR",
                    "status": 500,
                    "description": "서버 내부 에러",
                },
            ],
            "response_format": {
                "success": "bool - 요청 성공 여부",
                "error.code": "string - 에러 코드",
                "error.message": "string - 에러 메시지",
                "error.detail": "any - 추가 상세 정보 (선택)",
                "timestamp": "string - 에러 발생 시각 (ISO 8601)",
                "path": "string - 에러가 발생한 요청 경로",
            },
        },
    }


# ============================================================
# 루트 엔드포인트
# ============================================================
@app.get("/", tags=["기본"])
async def root():
    """
    API 루트 엔드포인트.
    이 챕터에서 다루는 에러 처리 주제 목록을 반환한다.
    """
    return {
        "chapter": "08 - 에러 처리 (Error Handling)",
        "topics": [
            "1. HTTPException: GET /items/{item_id}",
            "2. HTTPException + 커스텀 헤더: GET /items/{item_id}/with-header",
            "3. 커스텀 예외 (ItemNotFound): GET /products/{product_id}",
            "4. 커스텀 예외 (재고 부족): POST /orders/",
            "5. 유효성 검증 에러: POST /items/",
            "6. try/except 처리: GET /items/{item_id}/process",
            "7. 권한 에러: DELETE /items/{item_id}",
            "8. 예상치 못한 에러: GET /error/unexpected",
            "9. ValueError 테스트: GET /error/value-error",
            "10. 에러 카탈로그: GET /errors/catalog",
        ],
        "docs": "http://127.0.0.1:8000/docs",
    }
