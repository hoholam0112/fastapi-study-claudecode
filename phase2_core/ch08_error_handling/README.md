# Chapter 08: 에러 처리 (Error Handling)

## 학습 목표

- FastAPI의 `HTTPException`을 사용하여 적절한 HTTP 에러 응답을 반환한다
- 커스텀 예외 클래스를 정의하고 전용 예외 핸들러를 등록한다
- `RequestValidationError`를 오버라이드하여 일관된 에러 응답 포맷을 구성한다
- 전역 예외 핸들러를 구축하여 예상치 못한 에러도 안전하게 처리한다
- 통일된 에러 응답 모델을 설계하여 API의 예측 가능성을 높인다

## 핵심 개념

### 1. HTTPException

FastAPI에서 HTTP 에러를 반환하는 가장 기본적인 방법이다.

```python
from fastapi import HTTPException

raise HTTPException(
    status_code=404,
    detail="아이템을 찾을 수 없습니다",
    headers={"X-Error": "Not Found"},  # 선택적 커스텀 헤더
)
```

### 2. 커스텀 예외 클래스

비즈니스 로직에 특화된 예외를 정의하여 에러를 체계적으로 관리할 수 있다.

```python
class ItemNotFoundException(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id
        self.message = f"아이템 ID {item_id}을 찾을 수 없습니다"
```

### 3. 전역 예외 핸들러

`@app.exception_handler()`를 사용하여 특정 예외 타입에 대한 전역 핸들러를 등록한다.

```python
@app.exception_handler(ItemNotFoundException)
async def item_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": exc.message},
    )
```

### 4. RequestValidationError 오버라이드

Pydantic 검증 실패 시 반환되는 에러 형식을 커스터마이징할 수 있다.

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "유효성 검증 실패", "details": exc.errors()},
    )
```

### 5. 통일된 에러 응답 포맷

모든 에러 응답의 구조를 통일하면 클라이언트에서 에러를 일관되게 처리할 수 있다.

```json
{
    "success": false,
    "error": {
        "code": "ITEM_NOT_FOUND",
        "message": "아이템을 찾을 수 없습니다",
        "detail": "아이템 ID 999가 존재하지 않습니다"
    },
    "timestamp": "2025-01-01T12:00:00Z"
}
```

## 코드 실행 방법

```bash
# 챕터 디렉토리로 이동
cd phase2_core/ch08_error_handling

# 서버 실행
uvicorn main:app --reload

# API 문서 확인
# http://127.0.0.1:8000/docs
```

### 주요 엔드포인트 테스트

```bash
# 정상 아이템 조회
curl "http://127.0.0.1:8000/items/1"

# HTTPException (404) 테스트
curl "http://127.0.0.1:8000/items/999"

# HTTPException with 커스텀 헤더
curl -v "http://127.0.0.1:8000/items/999/with-header"

# 커스텀 예외 테스트
curl "http://127.0.0.1:8000/products/999"

# 유효성 검증 에러 테스트 (잘못된 타입)
curl "http://127.0.0.1:8000/items/abc"

# 유효성 검증 에러 테스트 (잘못된 요청 본문)
curl -X POST "http://127.0.0.1:8000/items/" \
  -H "Content-Type: application/json" \
  -d '{"name": "", "price": -100}'

# 전역 에러 핸들러 테스트 (예상치 못한 에러)
curl "http://127.0.0.1:8000/error/unexpected"

# 비즈니스 로직 에러 테스트
curl -X POST "http://127.0.0.1:8000/orders/" \
  -H "Content-Type: application/json" \
  -d '{"item_id": 1, "quantity": 999}'
```

## 실습 포인트

1. **HTTPException 활용**: 다양한 HTTP 상태 코드(400, 401, 403, 404, 409, 422, 500)에 맞는 에러를 발생시켜 보자
2. **커스텀 예외 계층 구조**: 기본 예외 클래스를 상속받아 여러 비즈니스 예외를 체계적으로 구성해 보자
3. **에러 응답 포맷 통일**: 모든 에러 응답이 동일한 JSON 구조를 따르도록 핸들러를 구성해 보자
4. **로깅 추가**: 예외 핸들러에서 에러 로깅을 추가하여 디버깅에 활용해 보자
5. **클라이언트 에러 처리**: API 에러 응답을 받았을 때 클라이언트에서 어떻게 처리하면 좋을지 고민해 보자

## 참고 자료

- [FastAPI 공식 문서 - Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [FastAPI 공식 문서 - Override Request Validation Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/#override-request-validation-exceptions)
- [HTTP 상태 코드 참고](https://developer.mozilla.org/ko/docs/Web/HTTP/Status)
