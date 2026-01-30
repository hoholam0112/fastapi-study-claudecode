"""
비동기 데이터베이스 설정 모듈

SQLAlchemy 2.0의 비동기 모드를 사용하여
AsyncEngine, AsyncSession을 설정합니다.
aiosqlite 드라이버를 사용하여 SQLite에 비동기로 접근합니다.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# 비동기 엔진 생성
# ---------------------------------------------------------------------------
# - "sqlite+aiosqlite" : SQLite용 비동기 드라이버 지정
# - echo=True : 실행되는 SQL 쿼리를 콘솔에 출력 (개발 환경 전용, 프로덕션에서는 False)
# - connect_args : SQLite는 단일 스레드에서만 접근 가능하므로 check_same_thread를 False로 설정
DATABASE_URL = "sqlite+aiosqlite:///./async_app.db"

async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
)

# ---------------------------------------------------------------------------
# 비동기 세션 팩토리 생성
# ---------------------------------------------------------------------------
# - async_sessionmaker : 비동기 세션을 생성하는 팩토리
# - expire_on_commit=False : 커밋 후에도 객체 속성에 접근할 수 있도록 설정
#   (비동기 환경에서는 커밋 후 속성 접근 시 추가 await가 필요하므로 False 권장)
# - class_ : 생성할 세션 클래스를 AsyncSession으로 지정
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# FastAPI 의존성 주입용 비동기 세션 제너레이터
# ---------------------------------------------------------------------------
async def get_db() -> AsyncSession:  # type: ignore[misc]
    """
    각 요청마다 새로운 비동기 데이터베이스 세션을 생성하고,
    요청이 완료되면 자동으로 세션을 닫습니다.

    사용 예시:
        @app.get("/users/")
        async def read_users(db: AsyncSession = Depends(get_db)):
            ...

    - `async with` 구문으로 세션의 생명주기를 안전하게 관리합니다.
    - 예외가 발생해도 세션이 올바르게 닫히는 것을 보장합니다.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # 예외 발생 시 롤백하여 데이터 정합성 유지
            await session.rollback()
            raise
