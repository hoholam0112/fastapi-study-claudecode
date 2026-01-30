# Chapter 12: 비동기 데이터베이스 (Async DB)

> **선택/심화 챕터**: 이 챕터는 비동기 프로그래밍과 SQLAlchemy 기초를 이해한 후 학습하는 것을 권장합니다.

## 학습 목표

1. SQLAlchemy 2.0의 비동기 모드를 이해하고 설정할 수 있다
2. `AsyncSession`을 사용하여 비동기 CRUD 작업을 수행할 수 있다
3. `aiosqlite` 드라이버를 활용한 비동기 SQLite 연동 방법을 익힌다
4. 비동기 엔진(`create_async_engine`) 설정과 세션 관리를 할 수 있다
5. FastAPI의 비동기 라이프사이클과 데이터베이스 초기화를 연결할 수 있다

## 핵심 개념

### SQLAlchemy 2.0 비동기 모드

SQLAlchemy 2.0부터 공식적으로 비동기(async/await) 패턴을 지원합니다.
기존 동기 방식과 동일한 ORM 모델을 사용하면서도, 비동기 I/O의 장점을 활용할 수 있습니다.

### 주요 구성 요소

| 구성 요소 | 설명 |
|-----------|------|
| `create_async_engine` | 비동기 데이터베이스 엔진 생성 |
| `async_sessionmaker` | 비동기 세션 팩토리 생성 |
| `AsyncSession` | 비동기 데이터베이스 세션 (await 사용) |
| `aiosqlite` | SQLite용 비동기 드라이버 |
| `DeclarativeBase` | SQLAlchemy 2.0 스타일 모델 베이스 클래스 |
| `Mapped` / `mapped_column` | 타입 힌트 기반 컬럼 선언 방식 |

### 동기 vs 비동기 비교

```python
# 동기 방식 (ch11)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine("sqlite:///./app.db")
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 비동기 방식 (ch12)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine("sqlite+aiosqlite:///./async_app.db")
AsyncSessionLocal = async_sessionmaker(bind=engine)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### 비동기 CRUD 패턴

```python
# 조회 (SELECT)
result = await session.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

# 생성 (INSERT)
session.add(new_user)
await session.commit()
await session.refresh(new_user)

# 수정 (UPDATE)
user.name = "새 이름"
await session.commit()

# 삭제 (DELETE)
await session.delete(user)
await session.commit()
```

## 파일 구조

```
ch12_async_db/
├── README.md          # 이 문서
├── database.py        # 비동기 데이터베이스 엔진 및 세션 설정
├── models.py          # SQLAlchemy 2.0 스타일 ORM 모델 정의
└── main.py            # FastAPI 애플리케이션 및 비동기 CRUD 엔드포인트
```

## 사전 준비

### 패키지 설치

```bash
pip install fastapi uvicorn sqlalchemy aiosqlite
```

- `sqlalchemy>=2.0`: 비동기 모드를 지원하는 SQLAlchemy 2.0 이상 필요
- `aiosqlite`: SQLite용 비동기 드라이버 (개발/학습 환경에 적합)

> **참고**: 프로덕션 환경에서는 `asyncpg`(PostgreSQL) 또는 `aiomysql`(MySQL)을 사용하는 것이 일반적입니다.

## 코드 실행 방법

```bash
# ch12_async_db 디렉토리에서 실행
cd phase3_database/ch12_async_db

# 개발 서버 실행 (자동 리로드 활성화)
uvicorn main:app --reload

# 특정 포트로 실행
uvicorn main:app --reload --port 8012
```

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 실습 포인트

### 1단계: 기본 동작 확인
- [ ] 서버를 실행하고 `async_app.db` 파일이 자동 생성되는지 확인
- [ ] Swagger UI에서 사용자(User) 생성 API 호출
- [ ] 생성한 사용자 조회 API로 데이터 확인

### 2단계: 비동기 CRUD 전체 흐름
- [ ] 사용자 생성 (POST /users/)
- [ ] 전체 사용자 목록 조회 (GET /users/)
- [ ] 특정 사용자 조회 (GET /users/{user_id})
- [ ] 아이템 생성 (POST /users/{user_id}/items/)
- [ ] 사용자 정보 수정 (PUT /users/{user_id})
- [ ] 사용자 삭제 (DELETE /users/{user_id})

### 3단계: 비동기 동작 이해
- [ ] `await session.execute()`와 동기 `session.query()`의 차이점 분석
- [ ] `async with` 컨텍스트 매니저를 통한 세션 관리 방식 이해
- [ ] 라이프사이클(`lifespan`)을 통한 테이블 자동 생성 과정 확인

### 4단계: 심화 실습
- [ ] 여러 요청을 동시에 보내서 비동기 처리 확인 (예: `curl` 병렬 실행)
- [ ] `selectinload`를 사용한 관계 데이터 즉시 로딩(eager loading) 실습
- [ ] 에러 발생 시 롤백(`rollback`) 동작 확인

## 참고 자료

- [SQLAlchemy 2.0 비동기 문서](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI 공식 문서 - SQL (Relational) Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [aiosqlite GitHub](https://github.com/omnilib/aiosqlite)
