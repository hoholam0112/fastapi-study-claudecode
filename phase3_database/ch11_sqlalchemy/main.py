"""
main.py - FastAPI 애플리케이션 (라우트 정의)

이 파일은 모든 모듈을 통합하여 HTTP 엔드포인트를 정의합니다.

구조:
    database.py → 데이터베이스 연결 설정
    models.py   → 테이블 정의 (SQLAlchemy)
    schemas.py  → 요청/응답 데이터 형태 (Pydantic)
    crud.py     → 데이터베이스 조작 함수
    main.py     → HTTP 엔드포인트 (이 파일)

실행 방법:
    uvicorn main:app --reload

API 문서:
    Swagger UI: http://127.0.0.1:8000/docs
    ReDoc:      http://127.0.0.1:8000/redoc
"""

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

# 같은 디렉토리의 모듈들을 임포트합니다
import crud
import models
import schemas
from database import SessionLocal, engine, get_db

# ============================================================
# 1. 데이터베이스 테이블 생성
# ============================================================
# Base.metadata.create_all()은 models.py에 정의된 모든 모델을 기반으로
# 데이터베이스에 테이블을 생성합니다.
# 이미 존재하는 테이블은 건너뛰고, 없는 테이블만 새로 만듭니다.
#
# 주의: 이 방식은 개발/학습용입니다.
# 프로덕션에서는 Alembic 마이그레이션을 사용하는 것을 권장합니다.
# (기존 테이블의 컬럼 추가/삭제 등의 변경은 이 방식으로 처리되지 않습니다)
models.Base.metadata.create_all(bind=engine)

# ============================================================
# 2. FastAPI 앱 인스턴스 생성
# ============================================================
app = FastAPI(
    title="SQLAlchemy 학습 API",
    description="FastAPI와 SQLAlchemy ORM을 활용한 CRUD API 예제",
    version="1.0.0",
)


# ============================================================
# 3. 사용자(User) 관련 엔드포인트
# ============================================================

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    새로운 사용자를 생성합니다.

    요청 본문(Request Body):
        - email: 사용자 이메일 (필수, 고유값)
        - password: 비밀번호 (필수)

    처리 흐름:
        1. 이메일 중복 확인
        2. 중복이면 400 에러 반환
        3. 중복이 아니면 사용자 생성 후 반환

    Depends(get_db) 설명:
        FastAPI의 의존성 주입 시스템이 get_db() 함수를 호출하여
        데이터베이스 세션을 자동으로 생성하고 주입합니다.
        요청 처리가 끝나면 세션을 자동으로 닫아줍니다.

    response_model 설명:
        응답 데이터를 schemas.User 형태로 자동 변환합니다.
        이를 통해 hashed_password 같은 민감한 필드가 응답에 포함되지 않습니다.
    """
    # 이메일 중복 확인
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="이미 등록된 이메일입니다.",
        )

    # 사용자 생성 후 반환
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    사용자 목록을 조회합니다.

    쿼리 파라미터:
        - skip: 건너뛸 레코드 수 (기본값: 0, 페이지네이션용)
        - limit: 최대 조회 수 (기본값: 100)

    사용 예시:
        GET /users/             → 처음 100명 조회
        GET /users/?skip=10     → 11번째부터 100명 조회
        GET /users/?limit=5     → 처음 5명만 조회
        GET /users/?skip=5&limit=5 → 6번째부터 5명 조회
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    특정 사용자를 ID로 조회합니다.

    경로 파라미터:
        - user_id: 조회할 사용자의 고유 ID

    에러 처리:
        해당 ID의 사용자가 없으면 404 에러를 반환합니다.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="사용자를 찾을 수 없습니다.",
        )
    return db_user


# ============================================================
# 4. 아이템(Item) 관련 엔드포인트
# ============================================================

@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int,
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
):
    """
    특정 사용자의 아이템을 생성합니다.

    경로 파라미터:
        - user_id: 아이템 소유자의 사용자 ID

    요청 본문:
        - title: 아이템 제목 (필수)
        - description: 아이템 설명 (선택)

    에러 처리:
        해당 ID의 사용자가 없으면 404 에러를 반환합니다.
    """
    # 사용자 존재 여부 확인
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="사용자를 찾을 수 없습니다.",
        )

    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    아이템 목록을 조회합니다.

    쿼리 파라미터:
        - skip: 건너뛸 레코드 수 (기본값: 0)
        - limit: 최대 조회 수 (기본값: 100)
    """
    items = crud.get_items(db, skip=skip, limit=limit)
    return items
