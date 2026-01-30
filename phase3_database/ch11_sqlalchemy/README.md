# Chapter 11: SQLAlchemy ORM과 FastAPI 통합

## 학습 목표

이 챕터를 완료하면 다음을 이해하고 구현할 수 있습니다:

1. **ORM(Object-Relational Mapping)** 개념과 왜 사용하는지 이해한다
2. **SQLAlchemy 2.0** 의 핵심 구성요소(엔진, 세션, 모델)를 설정할 수 있다
3. **세션 관리**와 FastAPI의 의존성 주입을 결합하는 패턴을 익힌다
4. **Alembic**을 활용한 데이터베이스 마이그레이션 개념을 이해한다
5. FastAPI와 SQLAlchemy를 통합하여 **완전한 CRUD API**를 구축할 수 있다

---

## 핵심 개념

### ORM이란?

ORM은 프로그래밍 언어의 객체(Object)와 관계형 데이터베이스의 테이블(Relation)을
자동으로 연결(Mapping)해주는 기술입니다. SQL을 직접 작성하는 대신,
파이썬 클래스와 메서드를 사용하여 데이터베이스를 조작합니다.

```
Python 클래스 (User)  <──ORM 매핑──>  데이터베이스 테이블 (users)
Python 인스턴스       <──ORM 매핑──>  테이블의 행 (row)
클래스 속성           <──ORM 매핑──>  테이블의 열 (column)
```

### SQLAlchemy 2.0

SQLAlchemy는 파이썬에서 가장 널리 사용되는 ORM 라이브러리입니다.
2.0 버전에서는 더 명확하고 타입 안전한 API를 제공합니다.

핵심 구성요소:
- **Engine**: 데이터베이스 연결을 관리하는 객체
- **Session**: 데이터베이스와의 대화 단위 (트랜잭션 관리)
- **Base**: 모든 ORM 모델의 부모 클래스
- **Model**: 데이터베이스 테이블에 매핑되는 파이썬 클래스

### 세션 관리와 yield 패턴

FastAPI에서는 `yield`를 사용하는 의존성 함수로 세션의 생명주기를 관리합니다.
요청이 들어오면 세션을 생성하고, 요청이 끝나면 세션을 닫습니다.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db  # 요청 처리 중 세션 사용
    finally:
        db.close()  # 요청 완료 후 세션 닫기
```

### Alembic 소개

Alembic은 SQLAlchemy를 위한 데이터베이스 마이그레이션 도구입니다.
모델이 변경되면 Alembic이 자동으로 마이그레이션 스크립트를 생성하고,
이를 통해 데이터베이스 스키마를 버전 관리할 수 있습니다.

주요 명령어:
```bash
alembic init alembic          # 초기화
alembic revision --autogenerate -m "설명"  # 마이그레이션 생성
alembic upgrade head          # 최신 버전으로 업그레이드
alembic downgrade -1          # 한 단계 롤백
```

> 이 챕터에서는 `Base.metadata.create_all()`로 테이블을 직접 생성합니다.
> 실제 프로덕션에서는 Alembic을 사용하는 것을 권장합니다.

---

## 프로젝트 파일 구조와 역할

```
ch11_sqlalchemy/
├── README.md        # 학습 가이드 (이 파일)
├── database.py      # 데이터베이스 연결 설정
├── models.py        # SQLAlchemy ORM 모델 (테이블 정의)
├── schemas.py       # Pydantic 스키마 (API 요청/응답 정의)
├── crud.py          # 데이터베이스 CRUD 함수
└── main.py          # FastAPI 애플리케이션 (라우트 정의)
```

### 각 파일의 역할과 관계

| 파일 | 역할 | 의존 관계 |
|------|------|-----------|
| `database.py` | DB 엔진, 세션, Base 클래스 설정 | 독립적 (의존 없음) |
| `models.py` | DB 테이블을 파이썬 클래스로 정의 | `database.py`의 Base를 상속 |
| `schemas.py` | API 입출력 데이터 형태 정의 | 독립적 (Pydantic만 사용) |
| `crud.py` | DB 읽기/쓰기 로직 구현 | `models.py`, `schemas.py` 사용 |
| `main.py` | HTTP 엔드포인트 정의 | 모든 파일을 통합 |

### 데이터 흐름

```
[클라이언트 요청]
       │
       v
   main.py (라우트)  ──── schemas.py로 요청 데이터 검증
       │
       v
   crud.py (비즈니스 로직)  ──── models.py로 DB 조작
       │
       v
   database.py (세션)  ──── 실제 DB와 통신
       │
       v
   [SQLite 파일]
```

### models.py vs schemas.py 차이점

이 두 파일을 분리하는 이유는 **관심사의 분리(Separation of Concerns)** 원칙 때문입니다:

- **models.py (SQLAlchemy 모델)**: 데이터베이스 테이블의 구조를 정의합니다.
  DB에 어떤 컬럼이 있고, 어떤 관계가 있는지를 기술합니다.
- **schemas.py (Pydantic 스키마)**: API를 통해 주고받는 데이터의 형태를 정의합니다.
  클라이언트가 보내는 데이터와 서버가 응답하는 데이터의 모양을 기술합니다.

예를 들어, `User` 모델에는 `hashed_password`가 있지만,
API 응답 스키마에서는 비밀번호를 노출하지 않습니다.

---

## 코드 실행 방법

### 1. 필요한 패키지 설치

```bash
pip install fastapi uvicorn sqlalchemy
```

### 2. 서버 실행

```bash
cd phase3_database/ch11_sqlalchemy
uvicorn main:app --reload
```

### 3. API 테스트

서버가 실행되면 브라우저에서 Swagger UI를 확인할 수 있습니다:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

#### 사용자 생성 (POST /users/)
```bash
curl -X POST "http://127.0.0.1:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

#### 사용자 목록 조회 (GET /users/)
```bash
curl "http://127.0.0.1:8000/users/"
```

#### 특정 사용자 조회 (GET /users/{user_id})
```bash
curl "http://127.0.0.1:8000/users/1"
```

#### 아이템 생성 (POST /users/{user_id}/items/)
```bash
curl -X POST "http://127.0.0.1:8000/users/1/items/" \
  -H "Content-Type: application/json" \
  -d '{"title": "첫 번째 아이템", "description": "아이템 설명입니다"}'
```

#### 아이템 목록 조회 (GET /items/)
```bash
curl "http://127.0.0.1:8000/items/"
```

---

## 실습 포인트

### 기본 실습
1. 서버를 실행하고 Swagger UI에서 각 API를 직접 호출해 보세요
2. `sql_app.db` 파일이 자동으로 생성되는 것을 확인하세요
3. 동일한 이메일로 사용자를 두 번 생성하면 어떤 에러가 발생하는지 확인하세요

### 심화 실습
4. `models.py`에 `created_at` 컬럼을 추가해 보세요 (힌트: `Column(DateTime, default=func.now())`)
5. `crud.py`에 사용자 삭제(`delete_user`) 함수를 작성해 보세요
6. `crud.py`에 아이템 수정(`update_item`) 함수를 작성해 보세요
7. `schemas.py`에 `ItemUpdate` 스키마를 추가하고, PATCH 엔드포인트를 만들어 보세요

### 도전 과제
8. SQLite 대신 PostgreSQL 연결 문자열로 변경해 보세요
9. Alembic을 설치하고 마이그레이션을 직접 실행해 보세요
10. 비동기(async) SQLAlchemy 세션으로 리팩토링해 보세요
