"""
database.py - 데이터베이스 연결 설정 모듈

이 파일은 SQLAlchemy의 핵심 구성요소를 설정합니다:
- Engine: 데이터베이스와의 실제 연결을 관리
- SessionLocal: 데이터베이스 세션을 생성하는 팩토리
- Base: 모든 ORM 모델이 상속할 기본 클래스
- get_db(): FastAPI 의존성 주입에 사용할 세션 제공 함수
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ============================================================
# 1. 데이터베이스 URL 설정
# ============================================================
# SQLite를 사용합니다. 파일 기반 DB로, 별도 서버 설치가 필요 없습니다.
# "./sql_app.db" 파일이 현재 디렉토리에 자동 생성됩니다.
#
# PostgreSQL 사용 시: "postgresql://user:password@localhost/dbname"
# MySQL 사용 시: "mysql+pymysql://user:password@localhost/dbname"
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# ============================================================
# 2. 엔진(Engine) 생성
# ============================================================
# 엔진은 데이터베이스와의 연결 풀(Connection Pool)을 관리합니다.
# connect_args={"check_same_thread": False}는 SQLite 전용 옵션입니다.
# SQLite는 기본적으로 하나의 스레드에서만 사용할 수 있지만,
# FastAPI는 여러 스레드를 사용하므로 이 제한을 해제해야 합니다.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 전용 설정
)

# ============================================================
# 3. 세션 팩토리(SessionLocal) 생성
# ============================================================
# sessionmaker는 세션 객체를 만드는 팩토리(공장)입니다.
# - autocommit=False: 자동 커밋 비활성화 (명시적으로 commit() 호출 필요)
# - autoflush=False: 자동 플러시 비활성화 (쿼리 전 자동 DB 반영 방지)
# - bind=engine: 이 세션이 사용할 엔진을 지정
#
# 세션은 "데이터베이스와의 대화"를 나타냅니다.
# 하나의 요청에 하나의 세션을 사용하는 것이 일반적인 패턴입니다.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ============================================================
# 4. Base 클래스 생성
# ============================================================
# declarative_base()는 ORM 모델의 기본 클래스를 생성합니다.
# models.py에서 정의하는 모든 모델 클래스는 이 Base를 상속받습니다.
# Base를 상속받은 클래스는 자동으로 SQLAlchemy가 관리하는 테이블로 인식됩니다.
Base = declarative_base()


# ============================================================
# 5. get_db() 의존성 함수 (yield 패턴)
# ============================================================
# FastAPI의 Depends()와 함께 사용하는 의존성 함수입니다.
# yield 패턴을 사용하여 세션의 생명주기를 관리합니다.
#
# 동작 순서:
# 1) 요청이 들어오면 SessionLocal()로 새 세션을 생성
# 2) yield로 세션을 라우트 함수에 전달 (요청 처리 중)
# 3) 요청 처리가 끝나면 finally 블록에서 세션을 닫음
#
# 이 패턴 덕분에 세션 닫기를 깜빡하는 실수를 방지할 수 있습니다.
def get_db():
    """
    데이터베이스 세션을 생성하고, 사용 후 자동으로 닫아주는 제너레이터.

    사용 예시:
        @app.get("/users/")
        def read_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db  # 이 시점에서 라우트 함수가 세션을 사용합니다
    finally:
        db.close()  # 요청 완료 후 반드시 세션을 닫습니다
