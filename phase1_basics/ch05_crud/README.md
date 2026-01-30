# Chapter 05 - 메모리 기반 CRUD API

## 학습 목표

- RESTful API의 설계 원칙과 라우팅 규칙을 이해한다
- HTTP 메서드(POST, GET, PUT, DELETE)와 CRUD 연산의 매핑 관계를 이해한다
- 인메모리 딕셔너리를 사용하여 완전한 CRUD API를 구현할 수 있다
- 페이지네이션(skip, limit)을 구현할 수 있다
- 적절한 HTTP 상태 코드와 에러 처리를 적용할 수 있다

## 핵심 개념

### 1. CRUD와 HTTP 메서드 매핑

CRUD는 데이터의 기본 4가지 연산을 의미하며, 각각 HTTP 메서드에 대응된다:

| CRUD | HTTP 메서드 | 엔드포인트 예시 | 설명 |
|------|-----------|---------------|------|
| **C**reate | POST | `POST /items/` | 새 리소스 생성 |
| **R**ead | GET | `GET /items/` | 리소스 목록 조회 |
| **R**ead | GET | `GET /items/{id}` | 리소스 단건 조회 |
| **U**pdate | PUT | `PUT /items/{id}` | 리소스 전체 수정 |
| **D**elete | DELETE | `DELETE /items/{id}` | 리소스 삭제 |

### 2. RESTful 라우팅 규칙

- **명사 사용**: URL에는 동사가 아닌 명사를 사용한다 (`/items/` O, `/getItems` X)
- **복수형 사용**: 컬렉션 리소스는 복수형으로 표현한다 (`/items/` O, `/item/` X)
- **계층 구조**: 리소스 간 관계를 URL 경로로 표현한다 (`/users/{id}/items/`)
- **소문자 사용**: URL은 소문자와 하이픈(-)을 사용한다

### 3. 요청/응답 모델 분리

실무에서는 하나의 리소스에 대해 여러 Pydantic 모델을 정의한다:

```
ItemCreate   → 생성 요청 (POST body)
ItemUpdate   → 수정 요청 (PUT body)
ItemResponse → 응답 (서버 → 클라이언트)
```

이렇게 분리하는 이유:
- 생성 시에는 `id`가 필요 없지만, 응답에는 포함되어야 한다
- 수정 시에는 모든 필드가 선택적(Optional)일 수 있다
- 응답에는 `created_at`, `updated_at` 등 서버에서 생성하는 필드가 포함된다

### 4. 페이지네이션

대량의 데이터를 한 번에 반환하면 성능 문제가 발생한다. `skip`과 `limit` 쿼리 파라미터로 페이지네이션을 구현한다:

```
GET /items/?skip=0&limit=10   → 1~10번째 아이템
GET /items/?skip=10&limit=10  → 11~20번째 아이템
GET /items/?skip=20&limit=10  → 21~30번째 아이템
```

### 5. 에러 처리

존재하지 않는 리소스에 접근할 때는 적절한 HTTP 상태 코드와 에러 메시지를 반환한다:

```python
if item_id not in db:
    raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")
```

## 코드 실행 방법

```bash
# ch05_crud 디렉토리로 이동
cd phase1_basics/ch05_crud

# 서버 실행
uvicorn main:app --reload

# 브라우저에서 API 문서 확인
# http://127.0.0.1:8000/docs
```

### curl로 CRUD 테스트하기

```bash
# 1. Create - 아이템 생성
curl -X POST http://127.0.0.1:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "노트북", "description": "맥북 프로 16인치", "price": 3690000}'

# 2. Read - 전체 목록 조회 (페이지네이션)
curl http://127.0.0.1:8000/items/?skip=0&limit=10

# 3. Read - 단건 조회
curl http://127.0.0.1:8000/items/1

# 4. Update - 아이템 수정
curl -X PUT http://127.0.0.1:8000/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "노트북 (수정)", "price": 3490000}'

# 5. Delete - 아이템 삭제
curl -X DELETE http://127.0.0.1:8000/items/1
```

## 실습 포인트

1. **CRUD 전체 흐름 확인**: Swagger UI에서 생성 → 조회 → 수정 → 삭제 순서로 전체 흐름을 실행해 본다
2. **페이지네이션 테스트**: 아이템을 5개 이상 생성한 후 `skip`과 `limit`을 변경하며 결과를 확인한다
3. **404 에러 확인**: 존재하지 않는 ID(예: 999)로 조회/수정/삭제를 시도하여 에러 응답을 확인한다
4. **부분 수정 테스트**: PUT 요청에서 일부 필드만 전송하여 나머지 필드가 어떻게 처리되는지 확인한다
5. **응답 모델 비교**: 생성 요청의 body와 응답의 필드 차이를 비교한다 (id, created_at 등)

### 추가 도전 과제

- `PATCH` 메서드를 추가하여 부분 수정(partial update) 기능을 구현해 보자
- 아이템에 `category` 필드를 추가하고, 카테고리별 필터링 기능을 구현해 보자
- 페이지네이션 응답에 `total`, `page`, `pages` 정보를 포함하는 래퍼 모델을 만들어 보자
- 중복 이름 검사 로직을 추가하여 409 Conflict 에러를 반환해 보자
