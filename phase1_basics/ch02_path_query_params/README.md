# Chapter 02 - Path 파라미터와 Query 파라미터

## 학습 목표

- Path 파라미터와 Query 파라미터의 차이점을 이해한다.
- Python 타입 힌트를 활용한 FastAPI의 자동 데이터 검증 방식을 익힌다.
- Enum 클래스를 사용하여 허용 가능한 값을 제한하는 방법을 익힌다.
- Path 파라미터와 Query 파라미터를 조합하여 유연한 API를 설계할 수 있다.

---

## 핵심 개념

### 1. Path 파라미터 (경로 매개변수)

URL 경로의 일부로 전달되는 값이다. 리소스를 **식별**하는 데 사용한다.

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

| 요청 URL | item_id 값 | 결과 |
|----------|-----------|------|
| `/items/42` | `42` (int) | 정상 응답 |
| `/items/abc` | - | **422 에러** (int로 변환 불가) |

핵심: 함수 매개변수에 `int`를 지정하면, FastAPI가 **자동으로 타입 변환 및 검증**을 수행한다.

### 2. Query 파라미터 (쿼리 매개변수)

URL의 `?` 뒤에 `key=value` 형태로 전달되는 값이다. 주로 **필터링, 페이지네이션, 정렬** 등에 사용한다.

```python
@app.get("/items")
def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

| 요청 URL | skip | limit | 비고 |
|----------|------|-------|------|
| `/items` | `0` | `10` | 기본값 적용 |
| `/items?skip=5` | `5` | `10` | skip만 지정 |
| `/items?skip=5&limit=20` | `5` | `20` | 둘 다 지정 |

### 3. 선택적(Optional) 파라미터

`None`을 기본값으로 지정하면 선택적 파라미터가 된다.

```python
from typing import Optional

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```

Python 3.10 이상에서는 `str | None = None` 문법도 사용 가능하다.

### 4. Enum을 활용한 값 제한

`str`과 `Enum`을 함께 상속하면, 허용 가능한 값의 범위를 제한할 수 있다.
Swagger UI에서는 자동으로 드롭다운 선택지로 표시된다.

```python
from enum import Enum

class CategoryName(str, Enum):
    electronics = "electronics"
    books = "books"
    clothing = "clothing"

@app.get("/categories/{category_name}")
def get_category(category_name: CategoryName):
    return {"category": category_name}
```

### 5. 타입 힌트에 따른 자동 검증

| 타입 힌트 | 예시 값 | 자동 처리 |
|----------|---------|----------|
| `int` | `"42"` → `42` | 문자열을 정수로 자동 변환 |
| `float` | `"3.14"` → `3.14` | 문자열을 실수로 자동 변환 |
| `bool` | `"true"` → `True` | yes/on/1/true 등을 불리언으로 변환 |
| `str` | `"hello"` → `"hello"` | 그대로 사용 |

변환에 실패하면 FastAPI는 **422 Unprocessable Entity** 에러를 자동으로 반환한다.

---

## 코드 실행 방법

```bash
# ch02 디렉토리로 이동
cd phase1_basics/ch02_path_query_params

# 개발 서버 실행
uvicorn main:app --reload
```

서버 실행 후 테스트할 URL 목록:

| URL | 설명 |
|-----|------|
| http://127.0.0.1:8000/docs | Swagger UI 문서 |
| http://127.0.0.1:8000/items/1 | Path 파라미터 (정수) |
| http://127.0.0.1:8000/items/abc | Path 파라미터 타입 에러 확인 |
| http://127.0.0.1:8000/items/?skip=0&limit=5 | Query 파라미터 |
| http://127.0.0.1:8000/items/1?q=검색어 | Path + Query 조합 |
| http://127.0.0.1:8000/categories/electronics | Enum 파라미터 |
| http://127.0.0.1:8000/categories/invalid | Enum 검증 에러 확인 |
| http://127.0.0.1:8000/products/1?category=books&in_stock=true | 복합 조합 |

---

## 실습 포인트

1. `/items/abc`에 접속하여 **422 에러 응답**의 구조를 살펴본다. FastAPI가 어떤 정보를 포함하여 에러를 반환하는지 확인한다.
2. Swagger UI(`/docs`)에서 Enum 파라미터가 **드롭다운**으로 표시되는 것을 확인한다.
3. Query 파라미터에 기본값을 다양하게 변경해 보고, 클라이언트가 값을 생략했을 때의 동작을 확인한다.
4. `bool` 타입의 Query 파라미터에 `true`, `yes`, `on`, `1` 등 다양한 값을 넣어 보고 모두 `True`로 변환되는지 테스트한다.
5. 새로운 Enum 클래스(예: `SortOrder`)를 만들어 정렬 기능을 추가해 본다.
