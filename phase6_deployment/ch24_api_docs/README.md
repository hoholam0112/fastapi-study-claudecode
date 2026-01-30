# Chapter 24: API 문서화와 버전 관리

## 학습 목표

- FastAPI의 OpenAPI 스펙 자동 생성 원리를 이해한다
- OpenAPI 메타데이터(제목, 설명, 연락처, 라이선스 등)를 커스터마이징할 수 있다
- Tags를 활용하여 API 엔드포인트를 논리적으로 그룹화한다
- API 버전 관리 전략(URL / Header / Query)의 장단점을 비교하고 구현한다
- Swagger UI를 커스터마이징하여 팀에 맞는 API 문서를 구성한다

## 핵심 개념

### 1. OpenAPI 스펙 커스터마이징

FastAPI는 코드를 기반으로 OpenAPI 3.1 스펙을 자동 생성한다. 다음 항목을 설정할 수 있다:

| 항목 | 설명 |
|------|------|
| `title` | API 이름 |
| `description` | API 상세 설명 (Markdown 지원) |
| `version` | API 버전 |
| `terms_of_service` | 서비스 이용 약관 URL |
| `contact` | 담당자 정보 (이름, URL, 이메일) |
| `license_info` | 라이선스 정보 |

### 2. Tags 구성

Tags를 사용하면 Swagger UI에서 엔드포인트를 논리적으로 그룹화하여 표시할 수 있다.

```python
tags_metadata = [
    {"name": "users", "description": "사용자 관리 API"},
    {"name": "products", "description": "상품 관리 API"},
]
```

- `tags_metadata`에 정의한 순서대로 Swagger UI에 표시된다
- 각 태그에 `externalDocs`를 추가하여 외부 문서 링크를 제공할 수 있다

### 3. API 버전 관리 전략

| 전략 | 예시 | 장점 | 단점 |
|------|------|------|------|
| **URL 경로** | `/api/v1/users` | 명확하고 직관적, 캐싱 용이 | URL이 변경됨 |
| **HTTP 헤더** | `X-API-Version: 2` | URL 깔끔, REST 원칙 부합 | 브라우저 테스트 어려움 |
| **쿼리 파라미터** | `/users?version=2` | 구현 간단 | URL 오염, 캐싱 복잡 |

가장 널리 사용되는 방식은 **URL 경로 기반 버전 관리**이다.

### 4. Swagger UI 커스터마이징

FastAPI는 Swagger UI와 ReDoc을 기본 제공한다:

- `/docs` - Swagger UI (인터랙티브 API 테스트 가능)
- `/redoc` - ReDoc (읽기 전용 문서)

커스터마이징 가능 항목:
- OpenAPI 스키마에 커스텀 필드 추가
- `deprecated=True`로 폐기 예정 엔드포인트 표시
- `response_description`으로 응답 설명 추가
- docstring을 활용한 상세 설명 표시

### 5. 응답 모델과 문서화

```python
@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={
        200: {"description": "사용자 정보 조회 성공"},
        404: {"description": "사용자를 찾을 수 없음"},
    },
)
```

- `response_model`로 응답 스키마를 자동 문서화
- `responses` 딕셔너리로 상태 코드별 설명 추가

## 코드 실행 방법

### 의존성 설치

```bash
pip install fastapi uvicorn
```

### 서버 실행

```bash
cd phase6_deployment/ch24_api_docs
uvicorn main:app --reload
```

### 문서 확인

```bash
# Swagger UI (인터랙티브 문서)
open http://localhost:8000/docs

# ReDoc (읽기 전용 문서)
open http://localhost:8000/redoc

# OpenAPI JSON 스펙 직접 확인
curl http://localhost:8000/openapi.json | python -m json.tool
```

### 주요 엔드포인트 테스트

```bash
# V1 API
curl http://localhost:8000/api/v1/users
curl http://localhost:8000/api/v1/users/1
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "홍길동", "email": "hong@example.com"}'

# V2 API (개선된 버전)
curl http://localhost:8000/api/v2/users
curl http://localhost:8000/api/v2/users/1

# 폐기 예정 엔드포인트
curl http://localhost:8000/api/v1/users/search?name=홍길동
```

## 실습 포인트

1. **Swagger UI 탐색**: `/docs`에 접속하여 태그별 그룹화, 엔드포인트 설명, 응답 스키마를 확인한다
2. **ReDoc 비교**: `/redoc`에 접속하여 Swagger UI와의 차이를 비교해본다
3. **V1 vs V2 비교**: 동일 기능의 V1과 V2 엔드포인트 차이를 관찰한다
4. **deprecated 표시 확인**: Swagger UI에서 폐기 예정 엔드포인트가 어떻게 표시되는지 확인한다
5. **OpenAPI JSON 분석**: `/openapi.json` 응답을 직접 확인하며 스펙 구조를 파악한다
6. **커스텀 태그 추가**: 새로운 태그 그룹과 엔드포인트를 직접 추가해본다
