# Chapter 03 - Request Body와 Pydantic 모델

## 학습 목표

- Pydantic `BaseModel`을 사용하여 요청 본문(Request Body)의 구조를 정의하는 방법을 익힌다.
- `Field`를 활용한 세밀한 데이터 검증(최소 길이, 범위 제한 등)을 수행할 수 있다.
- `field_validator`로 커스텀 검증 로직을 구현할 수 있다.
- 중첩 모델(Nested Model)을 설계하여 복잡한 데이터 구조를 표현할 수 있다.
- 여러 모델을 하나의 엔드포인트에서 동시에 수신하는 방법을 이해한다.

---

## 핵심 개념

### 1. Pydantic BaseModel이란?

Pydantic은 Python 타입 힌트를 활용한 **데이터 검증 및 직렬화 라이브러리**이다.
FastAPI는 Pydantic을 핵심 기반으로 사용하여 요청/응답 데이터를 자동으로 검증한다.

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False  # 기본값이 있으면 선택적 필드
```

| 특징 | 설명 |
|------|------|
| **자동 타입 변환** | `"42"` → `42` (str → int 자동 변환) |
| **자동 검증** | 타입이 맞지 않으면 422 에러 자동 반환 |
| **자동 문서화** | Swagger UI에 스키마가 자동으로 표시 |
| **IDE 지원** | 자동완성, 타입 체크 지원 |

### 2. Field를 활용한 상세 검증

`Field`를 사용하면 각 필드에 대해 더 세밀한 제약 조건을 설정할 수 있다.

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(
        ...,               # ... 은 필수 필드를 의미
        min_length=1,      # 최소 길이
        max_length=100,    # 최대 길이
        examples=["노트북"],
    )
    price: float = Field(
        ...,
        gt=0,              # gt: greater than (초과)
        le=10_000_000,     # le: less than or equal (이하)
        description="상품 가격 (원)",
    )
    quantity: int = Field(
        default=1,
        ge=1,              # ge: greater than or equal (이상)
        le=999,            # le: less than or equal (이하)
    )
```

| 매개변수 | 의미 | 예시 |
|---------|------|------|
| `gt` | ~보다 큼 (초과) | `gt=0` → 0 초과 |
| `ge` | ~보다 크거나 같음 (이상) | `ge=1` → 1 이상 |
| `lt` | ~보다 작음 (미만) | `lt=100` → 100 미만 |
| `le` | ~보다 작거나 같음 (이하) | `le=999` → 999 이하 |
| `min_length` | 문자열 최소 길이 | `min_length=1` |
| `max_length` | 문자열 최대 길이 | `max_length=100` |
| `pattern` | 정규표현식 패턴 | `pattern=r"^\d{3}-\d{4}$"` |

### 3. field_validator (커스텀 검증)

Pydantic v2에서는 `@field_validator`를 사용하여 커스텀 검증 로직을 구현한다.

```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("이메일 형식이 올바르지 않습니다")
        return v.lower()  # 검증 후 소문자로 변환하여 반환
```

**주의사항:**
- `@field_validator`는 반드시 `@classmethod`와 함께 사용한다.
- 검증 함수는 검증된 값을 반환(return)해야 한다.
- `ValueError` 또는 `AssertionError`를 발생시켜 검증 실패를 알린다.

### 4. 중첩 모델 (Nested Model)

모델 안에 다른 모델을 필드로 포함하여 복잡한 데이터 구조를 표현할 수 있다.

```python
class Address(BaseModel):
    city: str
    street: str
    zip_code: str

class User(BaseModel):
    name: str
    address: Address           # 단일 중첩 모델
    tags: list[str] = []       # 문자열 리스트
```

요청 JSON 예시:
```json
{
    "name": "홍길동",
    "address": {
        "city": "서울",
        "street": "강남대로 123",
        "zip_code": "06000"
    },
    "tags": ["VIP", "신규"]
}
```

### 5. Body로 여러 모델 수신

하나의 엔드포인트에서 여러 Pydantic 모델을 동시에 수신할 수 있다.

```python
from fastapi import Body

@app.post("/orders/")
def create_order(
    user: User,
    item: Item,
    note: str = Body(default="", title="메모"),
):
    ...
```

요청 JSON:
```json
{
    "user": { "name": "홍길동", ... },
    "item": { "name": "노트북", ... },
    "note": "빠른 배송 부탁드립니다"
}
```

---

## 코드 실행 방법

```bash
# ch03 디렉토리로 이동
cd phase1_basics/ch03_request_body

# 개발 서버 실행
uvicorn main:app --reload
```

### Swagger UI에서 테스트하기

1. http://127.0.0.1:8000/docs 에 접속한다.
2. 각 POST 엔드포인트의 **"Try it out"** 버튼을 클릭한다.
3. Request Body에 JSON 데이터를 입력하고 **"Execute"**를 클릭한다.
4. 검증 에러가 발생하는 경우를 테스트해 본다.

### curl로 테스트하기

```bash
# 아이템 생성
curl -X POST http://127.0.0.1:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "노트북", "price": 1200000, "quantity": 2, "description": "고성능 노트북"}'

# 사용자 생성 (중첩 모델)
curl -X POST http://127.0.0.1:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "홍길동", "email": "hong@example.com", "age": 30, "address": {"city": "서울", "district": "강남구", "street": "테헤란로 123", "zip_code": "06236"}}'
```

---

## 실습 포인트

1. Swagger UI에서 **잘못된 타입의 데이터**를 전송해 보고, 422 에러 응답의 상세 내용을 확인한다.
2. `Field`의 `min_length`, `ge`, `le` 등 **제약 조건의 경계값**을 테스트한다 (예: `ge=0`일 때 -1 전송).
3. `field_validator`에서 이메일 형식 검증이 동작하는지 `@` 없는 문자열로 테스트한다.
4. 중첩 모델에서 **내부 모델의 필드 하나를 빠뜨려** 보고 에러 메시지를 확인한다.
5. 새로운 Pydantic 모델을 직접 만들어 보고 (예: `Product`), POST 엔드포인트를 추가한다.
6. `model_config`에서 `json_schema_extra`를 설정하여 Swagger UI에 예제 데이터가 표시되는지 확인한다.
