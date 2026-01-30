"""
auth.py - 인증 핵심 로직

JWT 토큰 생성/검증, 비밀번호 해싱/검증, 사용자 인증 의존성을 정의한다.
이 모듈은 main.py에서 임포트하여 사용한다.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from schemas import TokenData, User, UserInDB


# ============================================================
# 상수 정의
# ============================================================

# JWT 서명에 사용되는 비밀 키 (운영 환경에서는 환경 변수로 관리해야 한다)
SECRET_KEY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# JWT 서명 알고리즘 (HS256 = HMAC + SHA-256)
ALGORITHM = "HS256"

# 액세스 토큰 만료 시간 (분 단위)
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ============================================================
# 비밀번호 해싱 설정
# ============================================================

# bcrypt 해싱 컨텍스트 생성
# - schemes: 사용할 해싱 알고리즘 목록
# - deprecated="auto": 기존 알고리즘을 자동으로 비활성화 처리
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# OAuth2 설정
# ============================================================

# OAuth2 Password Bearer 스킴 정의
# - tokenUrl: 토큰 발급 엔드포인트 경로 (Swagger UI 로그인 폼에서 사용)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ============================================================
# 인메모리 사용자 데이터베이스 (데모용)
# ============================================================

# 실제 운영 환경에서는 PostgreSQL, MongoDB 등 실제 DB를 사용해야 한다.
# 서버 재시작 시 데이터가 초기화된다는 점에 유의한다.
fake_users_db: dict[str, dict] = {}


# ============================================================
# 비밀번호 관련 함수
# ============================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 해싱된 비밀번호를 비교하여 일치 여부를 반환한다.

    Args:
        plain_password: 사용자가 입력한 평문 비밀번호
        hashed_password: 데이터베이스에 저장된 해싱된 비밀번호

    Returns:
        비밀번호가 일치하면 True, 불일치하면 False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    평문 비밀번호를 bcrypt로 해싱하여 반환한다.

    Args:
        password: 해싱할 평문 비밀번호

    Returns:
        bcrypt로 해싱된 비밀번호 문자열
    """
    return pwd_context.hash(password)


# ============================================================
# 사용자 조회 함수
# ============================================================

def get_user(db: dict, username: str) -> Optional[UserInDB]:
    """
    사용자명으로 데이터베이스에서 사용자를 조회한다.

    Args:
        db: 사용자 데이터베이스 (딕셔너리)
        username: 조회할 사용자명

    Returns:
        사용자가 존재하면 UserInDB 객체, 없으면 None
    """
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(db: dict, username: str, password: str) -> Optional[UserInDB]:
    """
    사용자 인증을 수행한다.
    사용자명으로 조회한 뒤, 비밀번호가 일치하는지 검증한다.

    Args:
        db: 사용자 데이터베이스 (딕셔너리)
        username: 로그인할 사용자명
        password: 로그인할 비밀번호 (평문)

    Returns:
        인증 성공 시 UserInDB 객체, 실패 시 None
    """
    # 사용자 존재 여부 확인
    user = get_user(db, username)
    if user is None:
        return None

    # 비밀번호 일치 여부 확인
    if not verify_password(password, user.hashed_password):
        return None

    return user


# ============================================================
# JWT 토큰 관련 함수
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    JWT 액세스 토큰을 생성한다.

    Args:
        data: 토큰 페이로드에 포함할 데이터 (예: {"sub": "username"})
        expires_delta: 토큰 만료 시간 (미지정 시 기본값 15분)

    Returns:
        인코딩된 JWT 토큰 문자열
    """
    # 원본 데이터를 변경하지 않도록 복사본을 생성한다
    to_encode = data.copy()

    # 만료 시간 설정
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 기본 만료 시간: 15분
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    # 만료 시간 클레임 추가
    to_encode.update({"exp": expire})

    # JWT 토큰 인코딩 및 반환
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ============================================================
# 인증 의존성 (Dependency)
# ============================================================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    현재 요청의 JWT 토큰을 검증하고 사용자 정보를 반환하는 의존성 함수.

    FastAPI의 Depends()를 통해 보호된 엔드포인트에서 사용한다.
    토큰이 유효하지 않거나 사용자가 존재하지 않으면 401 에러를 발생시킨다.

    Args:
        token: Authorization 헤더에서 추출된 Bearer 토큰

    Returns:
        인증된 사용자 정보 (User 객체)

    Raises:
        HTTPException(401): 토큰이 유효하지 않거나 사용자가 존재하지 않을 때
    """
    # 인증 실패 시 반환할 예외를 미리 정의한다
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="토큰 인증에 실패했습니다. 유효한 토큰을 제공해 주세요.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # JWT 토큰 디코딩
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 'sub' 클레임에서 사용자명 추출
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception

        # 토큰 데이터 객체 생성
        token_data = TokenData(username=username)

    except JWTError:
        # JWT 디코딩 실패 (만료, 서명 불일치, 형식 오류 등)
        raise credentials_exception

    # 데이터베이스에서 사용자 조회
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    현재 사용자가 활성 상태인지 추가로 검증하는 의존성 함수.

    비활성화된 계정(disabled=True)의 접근을 차단한다.

    Args:
        current_user: get_current_user 의존성에서 반환된 사용자

    Returns:
        활성 상태인 사용자 정보 (User 객체)

    Raises:
        HTTPException(400): 비활성화된 계정일 때
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 계정입니다. 관리자에게 문의해 주세요.",
        )
    return current_user
