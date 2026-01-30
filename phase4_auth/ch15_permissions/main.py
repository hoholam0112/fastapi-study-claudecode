"""
Chapter 15: 권한 관리 (Permissions)
- Role 기반 접근 제어 (RBAC)
- OAuth2 Scopes
- API Key 인증
- 권한 데코레이터 패턴
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import (
    APIKeyHeader,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

# ============================================================
# 설정 상수
# ============================================================

# JWT 토큰 서명에 사용할 비밀 키 (실제 운영에서는 환경변수로 관리해야 함)
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"  # JWT 서명 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 토큰 만료 시간 (분)

# API Key 인증에 사용할 키 (실제 운영에서는 환경변수로 관리해야 함)
VALID_API_KEYS = [
    "supersecretapikey123",
    "anotherapikey456",
]


# ============================================================
# 역할 정의 (Enum)
# ============================================================

class Role(str, Enum):
    """사용자 역할을 정의하는 열거형 클래스"""
    ADMIN = "admin"    # 관리자: 모든 권한
    USER = "user"      # 일반 사용자: 읽기/쓰기 권한
    VIEWER = "viewer"  # 조회자: 읽기 전용 권한


# ============================================================
# Pydantic 모델
# ============================================================

class Token(BaseModel):
    """토큰 응답 모델"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """토큰에서 추출한 데이터 모델"""
    username: str | None = None
    scopes: list[str] = []


class UserInDB(BaseModel):
    """데이터베이스에 저장된 사용자 모델 (비밀번호 해시 포함)"""
    username: str
    full_name: str
    email: str
    role: Role
    hashed_password: str
    disabled: bool = False
    scopes: list[str] = []  # 사용자에게 허용된 scope 목록


class UserResponse(BaseModel):
    """사용자 응답 모델 (비밀번호 제외)"""
    username: str
    full_name: str
    email: str
    role: Role
    disabled: bool
    scopes: list[str]


# ============================================================
# 비밀번호 해싱 유틸리티
# ============================================================

# bcrypt 기반 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 해시된 비밀번호를 비교하여 일치 여부 반환"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """평문 비밀번호를 bcrypt로 해싱하여 반환"""
    return pwd_context.hash(password)


# ============================================================
# In-Memory 사용자 데이터베이스
# ============================================================

# 테스트용 사용자 데이터 (역할별 계정)
fake_users_db: dict[str, dict] = {
    "admin": {
        "username": "admin",
        "full_name": "관리자",
        "email": "admin@example.com",
        "role": Role.ADMIN,
        "hashed_password": get_password_hash("admin1234"),
        "disabled": False,
        "scopes": ["items:read", "items:write", "admin"],
    },
    "user1": {
        "username": "user1",
        "full_name": "일반 사용자",
        "email": "user1@example.com",
        "role": Role.USER,
        "hashed_password": get_password_hash("user1234"),
        "disabled": False,
        "scopes": ["items:read", "items:write"],
    },
    "viewer1": {
        "username": "viewer1",
        "full_name": "조회 전용 사용자",
        "email": "viewer1@example.com",
        "role": Role.VIEWER,
        "hashed_password": get_password_hash("viewer1234"),
        "disabled": False,
        "scopes": ["items:read"],
    },
}

# 샘플 아이템 데이터
fake_items_db: list[dict] = [
    {"id": 1, "name": "노트북", "price": 1200000, "owner": "user1"},
    {"id": 2, "name": "키보드", "price": 150000, "owner": "admin"},
    {"id": 3, "name": "마우스", "price": 80000, "owner": "viewer1"},
]


# ============================================================
# 사용자 조회 및 인증 함수
# ============================================================

def get_user(db: dict, username: str) -> UserInDB | None:
    """데이터베이스에서 사용자명으로 사용자를 조회"""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(db: dict, username: str, password: str) -> UserInDB | None:
    """사용자명과 비밀번호로 인증을 수행. 실패 시 None 반환"""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ============================================================
# JWT 토큰 생성
# ============================================================

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """JWT 액세스 토큰 생성. 만료 시간과 함께 데이터를 인코딩"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ============================================================
# OAuth2 및 API Key 보안 스킴 설정
# ============================================================

# OAuth2 스킴: 사용 가능한 scope 목록 정의
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "items:read": "아이템 조회 권한",
        "items:write": "아이템 생성 및 수정 권한",
        "admin": "관리자 전용 기능 권한",
    },
)

# API Key 헤더 스킴: X-API-Key 헤더에서 키 추출
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ============================================================
# 의존성: 현재 사용자 조회 (OAuth2 + Scopes)
# ============================================================

async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserInDB:
    """
    JWT 토큰에서 현재 사용자를 추출하고 scope를 검증하는 의존성.
    - 토큰이 유효하지 않으면 401 에러 발생
    - 필요한 scope가 토큰에 없으면 401 에러 발생
    """
    # scope 정보를 포함한 인증 에러 메시지 구성
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        # JWT 토큰 디코딩
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        # 토큰에 포함된 scope 목록 추출
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except (JWTError, ValidationError):
        raise credentials_exception

    # 사용자 조회
    user = get_user(fake_users_db, token_data.username)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 사용자입니다",
        )

    # 요청된 엔드포인트에 필요한 scope가 토큰에 포함되어 있는지 검증
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이 작업에 필요한 권한이 부족합니다",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return user


async def get_current_active_user(
    current_user: Annotated[UserInDB, Security(get_current_user, scopes=[])],
) -> UserInDB:
    """활성 상태인 현재 사용자를 반환하는 의존성 (scope 검증 없음)"""
    return current_user


# ============================================================
# 의존성: Role 기반 접근 제어 (RBAC)
# ============================================================

def role_required(allowed_roles: list[Role]):
    """
    특정 역할만 접근을 허용하는 의존성 팩토리.
    허용된 역할 목록에 사용자의 역할이 포함되지 않으면 403 에러를 발생시킨다.

    사용 예시:
        @app.get("/admin/only", dependencies=[Depends(role_required([Role.ADMIN]))])
    """
    async def _role_checker(
        current_user: Annotated[UserInDB, Security(get_current_user, scopes=[])],
    ) -> UserInDB:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"접근 권한이 없습니다. 필요한 역할: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return _role_checker


# ============================================================
# 의존성: API Key 인증
# ============================================================

async def verify_api_key(
    api_key: Annotated[str | None, Depends(api_key_header)],
) -> str:
    """
    X-API-Key 헤더에서 API 키를 검증하는 의존성.
    키가 없거나 유효하지 않으면 401/403 에러를 발생시킨다.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key가 제공되지 않았습니다. X-API-Key 헤더를 확인하세요.",
        )
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 API Key입니다",
        )
    return api_key


# ============================================================
# FastAPI 앱 생성
# ============================================================

app = FastAPI(
    title="Chapter 15: 권한 관리",
    description="RBAC, OAuth2 Scopes, API Key 인증 예제",
    version="1.0.0",
)


# ============================================================
# 엔드포인트: 토큰 발급
# ============================================================

@app.post("/token", response_model=Token, tags=["인증"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    사용자명과 비밀번호로 로그인하여 JWT 액세스 토큰을 발급받는 엔드포인트.
    요청 시 scope를 지정하면, 사용자에게 허용된 scope 내에서만 토큰에 포함된다.
    """
    # 사용자 인증
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자명 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 요청된 scope 중 사용자에게 허용된 scope만 필터링
    granted_scopes = [
        scope for scope in form_data.scopes if scope in user.scopes
    ]

    # JWT 토큰 생성 (subject: 사용자명, scopes: 부여된 권한 목록)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": granted_scopes},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


# ============================================================
# 엔드포인트: Public (인증 불필요)
# ============================================================

@app.get("/", tags=["공개"])
async def root():
    """누구나 접근 가능한 공개 엔드포인트"""
    return {
        "message": "Chapter 15: 권한 관리 예제",
        "endpoints": {
            "공개": "/",
            "토큰 발급": "POST /token",
            "내 정보": "/users/me",
            "아이템 조회 (scope)": "/items",
            "아이템 생성 (scope)": "POST /items",
            "관리자 전용 (RBAC)": "/admin/users",
            "API Key 인증": "/apikey/data",
        },
    }


@app.get("/health", tags=["공개"])
async def health_check():
    """서버 상태 확인용 공개 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# ============================================================
# 엔드포인트: 현재 사용자 정보 (인증 필요, scope 불필요)
# ============================================================

@app.get("/users/me", response_model=UserResponse, tags=["사용자"])
async def read_users_me(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    """현재 로그인한 사용자의 정보를 반환 (모든 인증된 사용자 접근 가능)"""
    return current_user


# ============================================================
# 엔드포인트: OAuth2 Scopes 기반 접근 제어
# ============================================================

@app.get("/items", tags=["아이템 (Scope 기반)"])
async def read_items(
    current_user: Annotated[
        UserInDB, Security(get_current_user, scopes=["items:read"])
    ],
):
    """
    아이템 목록 조회 (items:read scope 필요).
    admin, user, viewer 모두 이 scope를 가지고 있어 조회 가능.
    """
    return {
        "items": fake_items_db,
        "requested_by": current_user.username,
        "role": current_user.role,
    }


@app.post("/items", tags=["아이템 (Scope 기반)"])
async def create_item(
    current_user: Annotated[
        UserInDB, Security(get_current_user, scopes=["items:write"])
    ],
    name: str,
    price: int,
):
    """
    새 아이템 생성 (items:write scope 필요).
    viewer는 이 scope가 없으므로 접근 불가.
    """
    new_item = {
        "id": len(fake_items_db) + 1,
        "name": name,
        "price": price,
        "owner": current_user.username,
    }
    fake_items_db.append(new_item)
    return {
        "message": "아이템이 생성되었습니다",
        "item": new_item,
        "created_by": current_user.username,
    }


# ============================================================
# 엔드포인트: Admin 전용 (RBAC + Scope)
# ============================================================

@app.get("/admin/users", tags=["관리자 전용 (RBAC)"])
async def admin_list_users(
    current_user: Annotated[
        UserInDB,
        Depends(role_required([Role.ADMIN])),
    ],
):
    """
    모든 사용자 목록 조회 (admin 역할만 허용).
    RBAC 의존성을 통해 역할을 검증한다.
    """
    users = []
    for username, user_data in fake_users_db.items():
        users.append({
            "username": username,
            "full_name": user_data["full_name"],
            "email": user_data["email"],
            "role": user_data["role"],
            "disabled": user_data["disabled"],
        })
    return {"users": users, "total": len(users)}


@app.delete("/admin/users/{username}", tags=["관리자 전용 (RBAC)"])
async def admin_delete_user(
    username: str,
    current_user: Annotated[
        UserInDB,
        Depends(role_required([Role.ADMIN])),
    ],
):
    """
    사용자 삭제 (admin 역할만 허용).
    자기 자신은 삭제할 수 없다.
    """
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신은 삭제할 수 없습니다",
        )
    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"사용자 '{username}'을(를) 찾을 수 없습니다",
        )
    deleted_user = fake_users_db.pop(username)
    return {
        "message": f"사용자 '{username}'이(가) 삭제되었습니다",
        "deleted_user": deleted_user["full_name"],
    }


@app.get("/admin/stats", tags=["관리자 전용 (RBAC)"])
async def admin_stats(
    current_user: Annotated[
        UserInDB,
        Security(get_current_user, scopes=["admin"]),
    ],
):
    """
    시스템 통계 조회 (admin scope 필요).
    OAuth2 Scope 방식으로 관리자 권한을 검증한다.
    """
    return {
        "total_users": len(fake_users_db),
        "total_items": len(fake_items_db),
        "roles_count": {
            role.value: sum(
                1 for u in fake_users_db.values() if u["role"] == role
            )
            for role in Role
        },
        "requested_by": current_user.username,
    }


# ============================================================
# 엔드포인트: User 역할 이상 접근 가능 (RBAC)
# ============================================================

@app.get("/dashboard", tags=["사용자 (RBAC)"])
async def user_dashboard(
    current_user: Annotated[
        UserInDB,
        Depends(role_required([Role.ADMIN, Role.USER])),
    ],
):
    """
    사용자 대시보드 (admin, user 역할만 허용, viewer는 접근 불가).
    """
    user_items = [
        item for item in fake_items_db if item["owner"] == current_user.username
    ]
    return {
        "user": current_user.username,
        "role": current_user.role,
        "my_items": user_items,
        "my_items_count": len(user_items),
    }


# ============================================================
# 엔드포인트: API Key 인증
# ============================================================

@app.get("/apikey/data", tags=["API Key 인증"])
async def get_data_with_api_key(
    api_key: Annotated[str, Depends(verify_api_key)],
):
    """
    API Key로 인증된 요청만 접근 가능한 엔드포인트.
    X-API-Key 헤더에 유효한 키를 포함해야 한다.
    """
    return {
        "message": "API Key 인증 성공",
        "data": {
            "total_items": len(fake_items_db),
            "total_users": len(fake_users_db),
            "items_summary": [
                {"name": item["name"], "price": item["price"]}
                for item in fake_items_db
            ],
        },
    }


@app.post("/apikey/webhook", tags=["API Key 인증"])
async def webhook_with_api_key(
    api_key: Annotated[str, Depends(verify_api_key)],
    event: str = "default",
):
    """
    외부 서비스에서 호출하는 웹훅 엔드포인트 (API Key 인증).
    서비스 간 통신에서 주로 사용되는 패턴이다.
    """
    return {
        "message": "웹훅 수신 완료",
        "event": event,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
