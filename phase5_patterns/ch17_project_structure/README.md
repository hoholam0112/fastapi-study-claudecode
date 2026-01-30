# Chapter 17: 프로젝트 구조 설계

## 학습 목표

- FastAPI 프로젝트의 확장 가능한 디렉토리 구조를 이해한다
- `APIRouter`를 활용하여 엔드포인트를 모듈별로 분리하는 방법을 익힌다
- **계층 분리 패턴** (Router -> Service/CRUD -> Model)을 적용한다
- `BaseSettings`를 사용한 환경 설정 관리 방법을 학습한다
- `__init__.py`의 역할과 Python 패키지 구조를 이해한다

---

## 핵심 개념

### 1. 프로젝트 구조 설계 원칙

대규모 FastAPI 애플리케이션은 단일 파일로 관리할 수 없다.
기능별, 계층별로 코드를 분리하면 **유지보수성**, **테스트 용이성**, **협업 효율성**이 크게 향상된다.

핵심 원칙:
- **단일 책임 원칙**: 각 모듈은 하나의 역할만 수행한다
- **관심사 분리**: 라우팅, 비즈니스 로직, 데이터 접근을 분리한다
- **의존성 방향**: 상위 계층이 하위 계층에 의존하며, 역방향 의존은 금지한다

### 2. APIRouter 사용법

`APIRouter`는 FastAPI 앱의 엔드포인트를 모듈별로 분리할 수 있게 해주는 핵심 도구이다.

```python
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def get_users():
    return [{"name": "홍길동"}]
```

메인 앱에서 `include_router()`로 결합한다:

```python
app.include_router(router, prefix="/api/v1")
```

### 3. 계층 분리 (Router -> Service/CRUD -> Model)

```
요청 흐름:
  Client -> Router(엔드포인트) -> Service/CRUD(비즈니스 로직) -> Model(데이터)
```

| 계층 | 역할 | 위치 |
|------|------|------|
| **Router** | HTTP 요청/응답 처리, 입력 검증 | `app/api/` |
| **Schema** | 요청/응답 데이터 형식 정의 (Pydantic) | `app/schemas/` |
| **Service/CRUD** | 비즈니스 로직, 데이터 조작 | `app/crud/` |
| **Model** | 데이터베이스 테이블 정의 (SQLAlchemy) | `app/models/` |
| **Core** | 설정, 보안, 공통 유틸리티 | `app/core/` |

### 4. BaseSettings 설정 관리

`pydantic-settings`의 `BaseSettings`를 사용하면 환경변수, `.env` 파일에서 설정을 자동으로 로드할 수 있다.

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "MyApp"
    DEBUG: bool = False

@lru_cache
def get_settings():
    return Settings()
```

`lru_cache`를 사용하여 설정 객체를 **싱글톤**처럼 관리한다.

### 5. `__init__.py`의 역할

- 해당 디렉토리를 **Python 패키지**로 인식시킨다
- 패키지 초기화 코드를 실행할 수 있다
- 외부에 공개할 모듈을 `__all__`로 지정할 수 있다
- 비어 있어도 반드시 존재해야 한다

---

## 디렉토리 구조

```
ch17_project_structure/
├── README.md                          # 이 문서
├── app/
│   ├── __init__.py                    # 앱 패키지 초기화
│   ├── main.py                        # FastAPI 앱 인스턴스, 라우터 결합
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                  # BaseSettings 환경 설정
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py              # v1 API 라우터 통합
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── users.py           # 사용자 엔드포인트
│   │           └── items.py           # 아이템 엔드포인트
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py                    # SQLAlchemy 사용자 모델 (참고용)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py                    # Pydantic 사용자 스키마
│   └── crud/
│       ├── __init__.py
│       └── user.py                    # 사용자 CRUD 함수
```

---

## 코드 실행 방법

### 사전 준비

```bash
pip install fastapi uvicorn pydantic-settings
```

### 서버 실행

`ch17_project_structure` 디렉토리에서 아래 명령어를 실행한다:

```bash
uvicorn app.main:app --reload
```

### API 확인

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 주요 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/v1/users/` | 전체 사용자 목록 조회 |
| `POST` | `/api/v1/users/` | 사용자 생성 |
| `GET` | `/api/v1/users/{user_id}` | 특정 사용자 조회 |
| `PUT` | `/api/v1/users/{user_id}` | 사용자 정보 수정 |
| `DELETE` | `/api/v1/users/{user_id}` | 사용자 삭제 |
| `GET` | `/api/v1/items/` | 전체 아이템 목록 조회 |
| `POST` | `/api/v1/items/` | 아이템 생성 |
| `GET` | `/api/v1/items/{item_id}` | 특정 아이템 조회 |
| `PUT` | `/api/v1/items/{item_id}` | 아이템 정보 수정 |
| `DELETE` | `/api/v1/items/{item_id}` | 아이템 삭제 |

---

## 실습 포인트

1. **구조 파악**: 각 파일의 역할과 import 경로를 추적해 보자
2. **라우터 분리**: `users.py`를 참고하여 새로운 `products` 엔드포인트를 추가해 보자
3. **계층 분리 실습**: `items` 엔드포인트에도 별도의 `schemas/item.py`와 `crud/item.py`를 만들어 보자
4. **설정 확장**: `config.py`에 `ALLOWED_ORIGINS`, `SECRET_KEY` 등 새 설정을 추가해 보자
5. **환경변수 테스트**: `.env` 파일을 만들고 `DATABASE_URL`을 변경하여 설정이 로드되는지 확인해 보자
6. **API 버전 관리**: `api/v2/` 디렉토리를 만들어 API 버전 관리 패턴을 직접 구현해 보자
