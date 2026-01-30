"""
models.py - SQLAlchemy ORM 모델 정의

이 파일은 데이터베이스 테이블을 파이썬 클래스로 정의합니다.
각 클래스는 하나의 테이블에 매핑되고, 클래스의 속성은 테이블의 컬럼에 매핑됩니다.

ORM 매핑 관계:
    Python 클래스  →  DB 테이블
    클래스 속성    →  테이블 컬럼
    클래스 인스턴스 →  테이블의 행(row)
    relationship  →  테이블 간 관계 (JOIN)
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

# database.py에서 정의한 Base 클래스를 가져옵니다.
# 모든 모델은 이 Base를 상속받아야 SQLAlchemy가 테이블로 인식합니다.
from database import Base


# ============================================================
# User 모델 - 사용자 테이블
# ============================================================
# __tablename__: 실제 DB에 생성될 테이블 이름
# Column(): 테이블의 컬럼(열)을 정의
# relationship(): 다른 테이블과의 관계를 정의 (실제 DB 컬럼은 아님)
class User(Base):
    """
    사용자(User) 테이블 모델

    하나의 사용자는 여러 개의 아이템을 소유할 수 있습니다 (1:N 관계).

    컬럼 설명:
    - id: 기본키(Primary Key), 자동 증가
    - email: 이메일 주소, 고유값(unique), 인덱스 생성
    - hashed_password: 해시된 비밀번호 (평문 저장 금지!)
    - is_active: 계정 활성화 여부, 기본값 True
    """
    __tablename__ = "users"  # 데이터베이스에 생성될 테이블 이름

    # --- 컬럼(Column) 정의 ---
    # primary_key=True: 이 컬럼을 기본키로 설정 (자동 증가)
    id = Column(Integer, primary_key=True, index=True)

    # unique=True: 중복 이메일 방지 (동일 이메일로 가입 불가)
    # index=True: 이메일로 빠르게 검색하기 위한 인덱스 생성
    email = Column(String, unique=True, index=True)

    # 비밀번호는 반드시 해시하여 저장해야 합니다.
    # 실제 프로덕션에서는 bcrypt 등의 해시 알고리즘을 사용합니다.
    hashed_password = Column(String)

    # 계정 활성화 여부 (비활성화된 사용자는 로그인 차단 가능)
    is_active = Column(Boolean, default=True)

    # --- 관계(Relationship) 정의 ---
    # relationship()은 실제 DB 컬럼이 아닙니다.
    # ORM 레벨에서 관련 객체에 편리하게 접근하기 위한 설정입니다.
    #
    # "Item": 관계를 맺을 대상 모델 클래스 이름 (문자열로 전달)
    # back_populates="owner": Item 모델의 'owner' 속성과 양방향 연결
    #
    # 사용 예시: user.items → 이 사용자가 소유한 모든 아이템 리스트
    items = relationship("Item", back_populates="owner")


# ============================================================
# Item 모델 - 아이템 테이블
# ============================================================
# User와 Item은 1:N(일대다) 관계입니다.
# 하나의 User가 여러 Item을 소유할 수 있습니다.
# ForeignKey를 통해 Item이 어떤 User에 속하는지 연결합니다.
class Item(Base):
    """
    아이템(Item) 테이블 모델

    각 아이템은 반드시 하나의 소유자(User)를 가집니다.

    컬럼 설명:
    - id: 기본키(Primary Key), 자동 증가
    - title: 아이템 제목, 인덱스 생성
    - description: 아이템 설명 (선택 사항)
    - owner_id: 소유자의 User ID (외래키)
    """
    __tablename__ = "items"  # 데이터베이스에 생성될 테이블 이름

    # --- 컬럼(Column) 정의 ---
    id = Column(Integer, primary_key=True, index=True)

    # 아이템 제목 (검색을 위한 인덱스 생성)
    title = Column(String, index=True)

    # 아이템 설명 (선택 사항이므로 nullable 기본값 사용)
    description = Column(String)

    # --- 외래키(Foreign Key) 정의 ---
    # ForeignKey("users.id"): users 테이블의 id 컬럼을 참조
    # 이 컬럼이 실제로 DB에 저장되는 관계 정보입니다.
    # "users.id"에서 "users"는 __tablename__이고, "id"는 컬럼 이름입니다.
    owner_id = Column(Integer, ForeignKey("users.id"))

    # --- 관계(Relationship) 정의 ---
    # back_populates="items": User 모델의 'items' 속성과 양방향 연결
    #
    # 사용 예시: item.owner → 이 아이템의 소유자 User 객체
    owner = relationship("User", back_populates="items")
