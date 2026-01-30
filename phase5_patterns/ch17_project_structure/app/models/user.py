"""
사용자 데이터베이스 모델 (참고용)

SQLAlchemy ORM을 사용한 사용자 테이블 정의이다.
이 데모에서는 실제 데이터베이스에 연결하지 않고,
프로젝트 구조에서 모델 계층이 어떤 역할을 하는지 보여주기 위한 참고 코드이다.

실제 프로젝트에서는 이 모델과 함께 database.py에서
엔진, 세션, Base 객체를 설정한다.
"""

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


# SQLAlchemy 2.0 스타일 선언적 기반 클래스
class Base(DeclarativeBase):
    """
    모든 SQLAlchemy 모델의 기반 클래스

    실제 프로젝트에서는 이 Base를 app/db/base.py 같은 별도 파일에 정의하고,
    모든 모델이 공유하도록 구성한다.
    """

    pass


class User(Base):
    """
    사용자 테이블 모델

    데이터베이스의 'users' 테이블에 매핑된다.
    각 컬럼은 테이블의 열(column)을 나타낸다.

    Note:
        이 데모에서는 실제 DB 연결 없이 구조 참고용으로만 사용한다.
        실제 프로젝트에서는 Alembic과 함께 마이그레이션을 관리한다.
    """

    # 테이블 이름 지정
    __tablename__ = "users"

    # 기본 키: 자동 증가하는 정수형 ID
    id = Column(Integer, primary_key=True, index=True, comment="사용자 고유 ID")

    # 사용자 이름: 유일한 값이어야 하며, 인덱스를 생성한다
    username = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="사용자 이름",
    )

    # 이메일: 유일한 값이어야 하며, 인덱스를 생성한다
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="이메일 주소",
    )

    # 해시된 비밀번호: 원본 비밀번호를 절대 저장하지 않는다
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="해시된 비밀번호",
    )

    # 계정 활성화 상태: 기본값은 True
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="계정 활성화 여부",
    )

    def __repr__(self) -> str:
        """디버그용 문자열 표현"""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
