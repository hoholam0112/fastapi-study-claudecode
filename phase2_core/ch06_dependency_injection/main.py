"""
Chapter 06: 의존성 주입 (Dependency Injection)

FastAPI의 Depends() 시스템을 활용한 의존성 주입 패턴을 학습한다.
함수 기반, 클래스 기반, yield 기반 의존성과 의존성 체이닝을 다룬다.

실행 방법:
    uvicorn main:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, Header, Query, APIRouter
from typing import Optional

# ============================================================
# FastAPI 앱 생성
# ============================================================
app = FastAPI(
    title="Chapter 06: 의존성 주입",
    description="FastAPI의 Depends() 시스템을 활용한 의존성 주입 학습",
    version="1.0.0",
)


# ============================================================
# 1. 함수 기반 의존성
# - 가장 기본적인 의존성 형태
# - 일반 함수를 Depends()에 전달하여 사용
# - 함수의 매개변수가 자동으로 요청 파라미터와 매핑됨
# ============================================================
def common_parameters(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="최대 반환 항목 수"),
) -> dict:
    """
    공통 페이지네이션 파라미터를 처리하는 의존성 함수.
    여러 엔드포인트에서 동일한 skip/limit 로직을 재사용할 수 있다.
    """
    return {"skip": skip, "limit": limit}


# 더미 아이템 데이터 (DB 대신 사용)
fake_items_db = [
    {"item_id": i, "name": f"아이템 {i}", "price": i * 1000}
    for i in range(1, 51)
]


@app.get("/items/", tags=["함수 기반 의존성"])
async def read_items(commons: dict = Depends(common_parameters)):
    """
    함수 기반 의존성 사용 예시.
    common_parameters 함수가 skip, limit을 처리하여 dict로 반환한다.
    """
    skip = commons["skip"]
    limit = commons["limit"]
    return {
        "message": "함수 기반 의존성으로 페이지네이션 처리",
        "skip": skip,
        "limit": limit,
        "items": fake_items_db[skip : skip + limit],
        "total": len(fake_items_db),
    }


# ============================================================
# 2. 클래스 기반 의존성
# - 클래스의 __init__ 매개변수가 요청 파라미터와 매핑됨
# - 상태를 가진 의존성 객체를 만들 수 있음
# - 타입 힌트와 자동완성이 더 잘 동작함
# ============================================================
class CommonQueryParams:
    """
    클래스 기반 의존성 예시.
    __init__의 매개변수가 자동으로 쿼리 파라미터로 인식된다.
    함수 기반보다 구조화된 형태로 여러 파라미터를 관리할 수 있다.
    """

    def __init__(
        self,
        q: Optional[str] = Query(None, description="검색어"),
        skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
        limit: int = Query(100, ge=1, le=1000, description="최대 반환 항목 수"),
    ):
        self.q = q
        self.skip = skip
        self.limit = limit


@app.get("/items-class/", tags=["클래스 기반 의존성"])
async def read_items_class(commons: CommonQueryParams = Depends(CommonQueryParams)):
    """
    클래스 기반 의존성 사용 예시.
    CommonQueryParams 인스턴스가 자동으로 생성되어 주입된다.
    """
    # 검색어가 있으면 필터링 적용
    results = fake_items_db
    if commons.q:
        results = [
            item for item in results if commons.q.lower() in item["name"].lower()
        ]

    # 페이지네이션 적용
    paginated = results[commons.skip : commons.skip + commons.limit]

    return {
        "message": "클래스 기반 의존성으로 검색 + 페이지네이션 처리",
        "query": commons.q,
        "skip": commons.skip,
        "limit": commons.limit,
        "items": paginated,
        "total": len(results),
    }


# Depends()에 클래스를 직접 전달하는 축약 표현
# Depends(CommonQueryParams)와 Depends()는 타입 힌트로부터 클래스를 추론함
@app.get("/items-class-shortcut/", tags=["클래스 기반 의존성"])
async def read_items_class_shortcut(commons: CommonQueryParams = Depends()):
    """
    클래스 기반 의존성의 축약 표현.
    타입 힌트(CommonQueryParams)로부터 의존성을 자동 추론한다.
    Depends(CommonQueryParams)와 동일하게 동작한다.
    """
    return {
        "message": "축약 표현 Depends() 사용",
        "query": commons.q,
        "skip": commons.skip,
        "limit": commons.limit,
    }


# ============================================================
# 3. yield 의존성 (리소스 관리)
# - yield 전: 리소스 생성 (setup)
# - yield: 리소스를 엔드포인트에 제공
# - yield 후 (finally): 리소스 정리 (cleanup)
# - DB 세션, 파일 핸들, 네트워크 연결 관리에 적합
# ============================================================

# 가짜 DB 세션 클래스 (실제 DB 대신 시뮬레이션)
class FakeDBSession:
    """데이터베이스 세션을 시뮬레이션하는 클래스."""

    def __init__(self):
        self.connected = False
        self.data = {
            1: {"id": 1, "name": "노트북", "price": 1500000},
            2: {"id": 2, "name": "키보드", "price": 150000},
            3: {"id": 3, "name": "마우스", "price": 80000},
        }

    def connect(self):
        """DB 연결 시뮬레이션."""
        self.connected = True
        print("[DB] 세션 연결됨")

    def close(self):
        """DB 연결 종료 시뮬레이션."""
        self.connected = False
        print("[DB] 세션 종료됨")

    def get_items(self) -> list:
        """모든 아이템 조회."""
        if not self.connected:
            raise RuntimeError("DB에 연결되지 않았습니다")
        return list(self.data.values())

    def get_item(self, item_id: int) -> Optional[dict]:
        """특정 아이템 조회."""
        if not self.connected:
            raise RuntimeError("DB에 연결되지 않았습니다")
        return self.data.get(item_id)


def get_db():
    """
    yield 의존성: DB 세션 생성 및 정리.

    흐름:
    1. DB 세션 생성 및 연결 (setup)
    2. yield로 세션을 엔드포인트에 제공
    3. 엔드포인트 처리 완료 후 세션 종료 (cleanup)

    try/finally를 사용하여 예외 발생 시에도 반드시 세션이 종료되도록 보장한다.
    """
    db = FakeDBSession()
    db.connect()  # setup: 리소스 생성
    try:
        yield db  # 리소스 제공: 엔드포인트에서 db를 사용
    finally:
        db.close()  # cleanup: 리소스 정리 (예외 발생 여부와 무관하게 실행)


@app.get("/db-items/", tags=["yield 의존성"])
async def read_db_items(db: FakeDBSession = Depends(get_db)):
    """
    yield 의존성 사용 예시.
    DB 세션이 자동으로 생성되고, 응답 후 자동으로 정리된다.
    """
    items = db.get_items()
    return {
        "message": "yield 의존성으로 DB 세션 관리",
        "db_connected": db.connected,
        "items": items,
    }


@app.get("/db-items/{item_id}", tags=["yield 의존성"])
async def read_db_item(item_id: int, db: FakeDBSession = Depends(get_db)):
    """
    특정 아이템 조회. 존재하지 않으면 404 에러를 반환한다.
    예외가 발생하더라도 DB 세션은 finally 블록에서 안전하게 종료된다.
    """
    item = db.get_item(item_id)
    if item is None:
        # 이 예외가 발생해도 get_db의 finally 블록이 실행되어 세션이 종료됨
        raise HTTPException(
            status_code=404,
            detail=f"아이템 ID {item_id}을(를) 찾을 수 없습니다",
        )
    return {"message": "DB에서 아이템 조회 성공", "item": item}


# ============================================================
# 4. 의존성 체이닝
# - 의존성이 다른 의존성에 의존하는 구조
# - 인증/인가 파이프라인에 자주 사용됨
# - 체인: verify_token -> get_current_user -> get_active_user
# ============================================================

# 가짜 사용자 데이터베이스
fake_users_db = {
    "alice": {
        "username": "alice",
        "full_name": "Alice Kim",
        "email": "alice@example.com",
        "is_active": True,
    },
    "bob": {
        "username": "bob",
        "full_name": "Bob Lee",
        "email": "bob@example.com",
        "is_active": True,
    },
    "charlie": {
        "username": "charlie",
        "full_name": "Charlie Park",
        "email": "charlie@example.com",
        "is_active": False,  # 비활성 사용자
    },
}

# 토큰 -> 사용자명 매핑 (실제로는 JWT 등을 사용)
fake_token_db = {
    "fake-secret-token": "alice",
    "bob-token": "bob",
    "charlie-token": "charlie",
}


async def verify_token(x_token: str = Header(..., description="인증 토큰")):
    """
    의존성 체인 1단계: 토큰 검증.
    요청 헤더에서 X-Token을 추출하여 유효성을 검증한다.
    유효하지 않은 토큰이면 401 에러를 발생시킨다.
    """
    if x_token not in fake_token_db:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 인증 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 토큰에 매핑된 사용자명 반환
    return fake_token_db[x_token]


async def get_current_user(username: str = Depends(verify_token)):
    """
    의존성 체인 2단계: 현재 사용자 조회.
    verify_token에서 반환된 사용자명으로 사용자 정보를 조회한다.
    사용자가 존재하지 않으면 404 에러를 발생시킨다.
    """
    user = fake_users_db.get(username)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail=f"사용자 '{username}'을(를) 찾을 수 없습니다",
        )
    return user


async def get_active_user(current_user: dict = Depends(get_current_user)):
    """
    의존성 체인 3단계: 활성 사용자 확인.
    get_current_user에서 반환된 사용자가 활성 상태인지 확인한다.
    비활성 사용자이면 403 에러를 발생시킨다.
    """
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=403,
            detail="비활성화된 사용자입니다. 관리자에게 문의하세요.",
        )
    return current_user


@app.get("/users/me", tags=["의존성 체이닝"])
async def read_current_user(user: dict = Depends(get_active_user)):
    """
    의존성 체이닝 전체 흐름 시연.

    실행 순서:
    1. verify_token: X-Token 헤더에서 토큰 검증
    2. get_current_user: 토큰으로 사용자 조회
    3. get_active_user: 사용자 활성 상태 확인
    4. 엔드포인트: 사용자 정보 반환

    각 단계에서 검증 실패 시 즉시 에러 응답을 반환한다.
    """
    return {
        "message": "의존성 체이닝을 통해 인증된 활성 사용자",
        "user": user,
    }


@app.get("/users/me/items", tags=["의존성 체이닝"])
async def read_current_user_items(user: dict = Depends(get_active_user)):
    """
    동일한 인증 체인을 다른 엔드포인트에서 재사용하는 예시.
    의존성 체이닝의 핵심 장점: 인증 로직을 한 번만 작성하고 여러 곳에서 재사용.
    """
    # 사용자별 아이템 시뮬레이션
    user_items = [
        {"item_id": 1, "name": f"{user['username']}의 아이템 1"},
        {"item_id": 2, "name": f"{user['username']}의 아이템 2"},
    ]
    return {
        "message": f"{user['full_name']}님의 아이템 목록",
        "owner": user["username"],
        "items": user_items,
    }


# ============================================================
# 5. 라우터 레벨 의존성
# - APIRouter에 dependencies 매개변수로 의존성을 지정
# - 해당 라우터의 모든 엔드포인트에 자동 적용됨
# - 인증이 필요한 관리자 페이지 등에 유용
# ============================================================

# 관리자 전용 토큰 검증 의존성
async def verify_admin_token(x_token: str = Header(..., description="관리자 인증 토큰")):
    """
    관리자 전용 토큰 검증.
    일반 토큰 검증에 추가로 관리자 권한까지 확인한다.
    """
    if x_token not in fake_token_db:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
    username = fake_token_db[x_token]
    # alice만 관리자로 설정 (간단한 권한 체크 시뮬레이션)
    if username != "alice":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    return username


# 라우터 생성 시 dependencies 매개변수에 의존성 목록 전달
# 이 라우터의 모든 엔드포인트에 verify_admin_token이 자동 적용됨
admin_router = APIRouter(
    prefix="/admin",
    tags=["라우터 레벨 의존성 (관리자)"],
    dependencies=[Depends(verify_admin_token)],
)


@admin_router.get("/dashboard")
async def admin_dashboard():
    """
    관리자 대시보드.
    라우터 레벨 의존성에 의해 관리자 토큰이 자동으로 검증된다.
    엔드포인트 함수에서 별도로 의존성을 선언할 필요가 없다.
    """
    return {
        "message": "관리자 대시보드",
        "stats": {
            "total_users": len(fake_users_db),
            "active_users": sum(1 for u in fake_users_db.values() if u["is_active"]),
            "total_items": len(fake_items_db),
        },
    }


@admin_router.get("/users")
async def admin_list_users():
    """
    전체 사용자 목록 조회 (관리자 전용).
    라우터 레벨 의존성 덕분에 자동으로 관리자 인증이 적용된다.
    """
    return {
        "message": "전체 사용자 목록 (관리자 전용)",
        "users": list(fake_users_db.values()),
    }


# 라우터를 앱에 등록
app.include_router(admin_router)


# ============================================================
# 루트 엔드포인트
# ============================================================
@app.get("/", tags=["기본"])
async def root():
    """
    API 루트 엔드포인트.
    이 챕터에서 다루는 의존성 주입 패턴의 목록을 반환한다.
    """
    return {
        "chapter": "06 - 의존성 주입 (Dependency Injection)",
        "topics": [
            "1. 함수 기반 의존성: GET /items/",
            "2. 클래스 기반 의존성: GET /items-class/",
            "3. 클래스 의존성 축약: GET /items-class-shortcut/",
            "4. yield 의존성 (DB 세션): GET /db-items/",
            "5. yield 의존성 (개별 조회): GET /db-items/{item_id}",
            "6. 의존성 체이닝 (인증): GET /users/me",
            "7. 체이닝 재사용: GET /users/me/items",
            "8. 라우터 레벨 의존성: GET /admin/dashboard",
            "9. 라우터 레벨 의존성: GET /admin/users",
        ],
        "docs": "http://127.0.0.1:8000/docs",
    }
