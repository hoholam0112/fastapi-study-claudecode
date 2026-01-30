"""
SQLAlchemy 2.0 스타일 ORM 모델 정의

DeclarativeBase, Mapped, mapped_column을 사용하여
타입 힌트 기반의 현대적인 모델을 정의합니다.
비동기 모드에서도 동일한 모델 구조를 사용할 수 있습니다.
"""

from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# ---------------------------------------------------------------------------
# 베이스 클래스 정의 (SQLAlchemy 2.0 스타일)
# ---------------------------------------------------------------------------
# - 기존의 declarative_base() 함수 대신 DeclarativeBase를 상속하여 사용
# - 모든 ORM 모델은 이 Base 클래스를 상속받아야 합니다
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# 사용자(User) 모델
# ---------------------------------------------------------------------------
class User(Base):
    """
    사용자 테이블 모델

    Mapped[타입] : 컬럼의 Python 타입을 선언 (타입 힌트와 ORM 매핑을 동시에 처리)
    mapped_column() : 컬럼의 상세 옵션을 설정 (인덱스, 유니크, 기본값 등)
    """

    __tablename__ = "users"

    # 기본 키 - 자동 증가 정수
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 이메일 - 유니크 제약조건, 인덱스 설정
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    # 사용자 이름 - 인덱스 설정
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # 활성 상태 - 기본값 True (비활성화된 사용자를 소프트 삭제 처리할 때 사용)
    is_active: Mapped[bool] = mapped_column(default=True)

    # ---------------------------------------------------------------------------
    # 관계 설정 (1:N - 한 사용자가 여러 아이템을 소유)
    # ---------------------------------------------------------------------------
    # - back_populates : 양방향 관계 설정 (Item.owner와 연결)
    # - lazy="selectin" : 비동기 환경에서 관계 데이터를 즉시 로딩
    #   (비동기에서는 lazy loading이 기본적으로 동작하지 않으므로 selectin 권장)
    # - cascade : 사용자 삭제 시 연관된 아이템도 함께 삭제
    items: Mapped[list["Item"]] = relationship(
        back_populates="owner",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"


# ---------------------------------------------------------------------------
# 아이템(Item) 모델
# ---------------------------------------------------------------------------
class Item(Base):
    """
    아이템 테이블 모델

    사용자가 소유하는 아이템을 나타내며,
    외래 키(ForeignKey)를 통해 User 테이블과 연결됩니다.
    """

    __tablename__ = "items"

    # 기본 키 - 자동 증가 정수
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 아이템 제목
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)

    # 아이템 설명 - 선택 사항 (Optional)
    description: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    # ---------------------------------------------------------------------------
    # 외래 키 - 소유자(User)의 id를 참조
    # ---------------------------------------------------------------------------
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    # ---------------------------------------------------------------------------
    # 관계 설정 (N:1 - 여러 아이템이 한 사용자에게 속함)
    # ---------------------------------------------------------------------------
    # - back_populates : 양방향 관계 설정 (User.items와 연결)
    # - lazy="selectin" : 비동기 환경에서 관계 데이터를 즉시 로딩
    owner: Mapped["User"] = relationship(
        back_populates="items",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, title='{self.title}', owner_id={self.owner_id})>"
