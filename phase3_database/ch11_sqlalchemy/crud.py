"""
crud.py - 데이터베이스 CRUD(생성/읽기/수정/삭제) 함수 모듈

CRUD는 데이터베이스의 4가지 기본 연산을 의미합니다:
    C - Create (생성): 새로운 레코드 추가
    R - Read   (읽기): 기존 레코드 조회
    U - Update (수정): 기존 레코드 변경
    D - Delete (삭제): 기존 레코드 제거

이 파일은 비즈니스 로직과 데이터베이스 접근 로직을 분리합니다.
main.py(라우트)에서 직접 DB를 조작하지 않고, 이 파일의 함수를 호출합니다.
이렇게 하면 테스트와 유지보수가 쉬워집니다.
"""

from sqlalchemy.orm import Session

import models
import schemas


# ============================================================
# 사용자(User) 관련 CRUD 함수
# ============================================================

def get_user(db: Session, user_id: int):
    """
    사용자 ID로 단일 사용자를 조회합니다.

    매개변수:
        db: 데이터베이스 세션 (FastAPI의 Depends를 통해 주입)
        user_id: 조회할 사용자의 고유 ID

    반환값:
        User 객체 또는 None (해당 ID의 사용자가 없는 경우)

    SQLAlchemy 메서드 설명:
        query(Model): 해당 모델(테이블)에 대한 쿼리 시작
        filter(조건): WHERE 절에 해당하는 필터링
        first(): 첫 번째 결과만 반환 (없으면 None)
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """
    이메일 주소로 사용자를 조회합니다.

    주로 회원가입 시 이미 등록된 이메일인지 확인하는 데 사용합니다.

    매개변수:
        db: 데이터베이스 세션
        email: 조회할 이메일 주소

    반환값:
        User 객체 또는 None
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    사용자 목록을 조회합니다 (페이지네이션 지원).

    매개변수:
        db: 데이터베이스 세션
        skip: 건너뛸 레코드 수 (기본값: 0, SQL의 OFFSET에 해당)
        limit: 최대 조회 수 (기본값: 100, SQL의 LIMIT에 해당)

    반환값:
        User 객체 리스트

    생성되는 SQL:
        SELECT * FROM users OFFSET {skip} LIMIT {limit}
    """
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    """
    새로운 사용자를 생성합니다.

    매개변수:
        db: 데이터베이스 세션
        user: 사용자 생성 스키마 (email, password 포함)

    반환값:
        생성된 User 객체 (id가 자동 부여된 상태)

    처리 순서:
        1. 비밀번호를 해시 처리 (여기서는 학습용으로 가짜 해시 사용)
        2. User ORM 객체 생성
        3. 세션에 추가 (db.add) → 아직 DB에 저장되지 않음
        4. 커밋 (db.commit) → 실제 DB에 저장 (INSERT 실행)
        5. 리프레시 (db.refresh) → DB가 생성한 id 등의 값을 객체에 반영

    주의: 실제 프로덕션에서는 반드시 bcrypt 등의 안전한 해시 알고리즘을 사용하세요.
    """
    # 가짜 해시 처리 (학습용 - 실제로는 bcrypt, argon2 등을 사용해야 합니다!)
    fake_hashed_password = "fakehashed_" + user.password

    # SQLAlchemy ORM 모델 인스턴스 생성
    # Pydantic 스키마(user)의 데이터를 ORM 모델(db_user)로 변환합니다
    db_user = models.User(
        email=user.email,
        hashed_password=fake_hashed_password,
    )

    # 세션에 새 객체 추가 (INSERT 준비)
    db.add(db_user)

    # 트랜잭션 커밋 (실제 DB에 반영)
    db.commit()

    # DB에서 최신 데이터 다시 읽기 (자동 생성된 id 값 등을 가져옴)
    db.refresh(db_user)

    return db_user


# ============================================================
# 아이템(Item) 관련 CRUD 함수
# ============================================================

def get_items(db: Session, skip: int = 0, limit: int = 100):
    """
    아이템 목록을 조회합니다 (페이지네이션 지원).

    매개변수:
        db: 데이터베이스 세션
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 최대 조회 수 (기본값: 100)

    반환값:
        Item 객체 리스트
    """
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    """
    특정 사용자의 아이템을 생성합니다.

    매개변수:
        db: 데이터베이스 세션
        item: 아이템 생성 스키마 (title, description 포함)
        user_id: 아이템 소유자의 사용자 ID

    반환값:
        생성된 Item 객체

    **model_dump() 활용:
        item.model_dump()은 Pydantic 모델을 딕셔너리로 변환합니다.
        예: ItemCreate(title="책", description="파이썬 책")
            → {"title": "책", "description": "파이썬 책"}

        **를 사용하여 딕셔너리를 키워드 인자로 풀어서 전달합니다.
        추가로 owner_id를 별도로 지정합니다.
    """
    # Pydantic 스키마를 딕셔너리로 변환 후, ORM 모델 인스턴스 생성
    # **item.model_dump()은 {title: "...", description: "..."}를 풀어서 전달
    db_item = models.Item(**item.model_dump(), owner_id=user_id)

    # 세션에 추가 → 커밋 → 리프레시 (create_user와 동일한 패턴)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item
