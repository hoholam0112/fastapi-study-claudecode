"""
Chapter 16: 보안 강화 (Security Hardening)
- 환경변수 관리 (pydantic-settings)
- Rate Limiting (요청 속도 제한)
- 보안 헤더 미들웨어
- CORS 설정
- 보호된 엔드포인트 예제
"""

import time
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware

from config import Settings, get_settings

# ============================================================
# In-Memory Rate Limiter
# ============================================================

# 클라이언트별 요청 기록을 저장하는 딕셔너리
# 키: 클라이언트 IP, 값: 요청 타임스탬프 목록
rate_limit_store: dict[str, list[float]] = {}


def get_client_ip(request: Request) -> str:
    """
    요청에서 클라이언트 IP를 추출한다.
    리버스 프록시를 사용하는 경우 X-Forwarded-For 헤더를 우선 확인한다.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For에는 여러 IP가 쉼표로 구분되어 있을 수 있다
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """
    요청 속도를 제한하는 의존성 함수.

    동작 방식:
    1. 클라이언트 IP를 기반으로 요청 기록을 관리한다.
    2. 현재 시간 기준으로 시간 창(window) 내의 요청만 유지한다.
    3. 시간 창 내 요청 수가 제한을 초과하면 429 에러를 반환한다.

    주의: In-Memory 방식이므로 서버 재시작 시 기록이 초기화되며,
    다중 서버 환경에서는 Redis 등 외부 저장소를 사용해야 한다.
    """
    client_ip = get_client_ip(request)
    current_time = time.time()
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    max_requests = settings.RATE_LIMIT_REQUESTS

    # 해당 클라이언트의 요청 기록이 없으면 초기화
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []

    # 시간 창 밖의 오래된 요청 기록을 제거
    rate_limit_store[client_ip] = [
        timestamp
        for timestamp in rate_limit_store[client_ip]
        if current_time - timestamp < window
    ]

    # 현재 시간 창 내 요청 수 확인
    if len(rate_limit_store[client_ip]) >= max_requests:
        # 가장 오래된 요청 시간을 기준으로 재시도 가능 시간 계산
        oldest_request = rate_limit_store[client_ip][0]
        retry_after = int(window - (current_time - oldest_request)) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"요청 횟수가 제한을 초과했습니다. {retry_after}초 후에 다시 시도하세요.",
            headers={"Retry-After": str(retry_after)},
        )

    # 현재 요청 타임스탬프 기록
    rate_limit_store[client_ip].append(current_time)


# ============================================================
# 보안 헤더 미들웨어
# ============================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    모든 HTTP 응답에 보안 관련 헤더를 자동으로 추가하는 미들웨어.

    각 헤더의 역할:
    - X-Content-Type-Options: MIME 타입 스니핑 방지
    - X-Frame-Options: 클릭재킹 방어 (iframe 삽입 차단)
    - X-XSS-Protection: 브라우저의 XSS 필터 활성화
    - Strict-Transport-Security: HTTPS 강제 (HSTS)
    - Content-Security-Policy: 리소스 로드 정책
    - Referrer-Policy: 리퍼러 정보 전송 제어
    - Permissions-Policy: 브라우저 기능 접근 제어
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # MIME 타입 스니핑 방지: 브라우저가 Content-Type을 무시하고
        # 콘텐츠를 추론하는 것을 차단
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 클릭재킹 방어: 페이지가 iframe에 삽입되는 것을 차단
        response.headers["X-Frame-Options"] = "DENY"

        # XSS 필터: 브라우저의 내장 XSS 필터를 활성화하고
        # 공격 감지 시 페이지 렌더링을 차단
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS: 브라우저가 이후 1년간 HTTPS로만 접속하도록 강제
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # CSP: 같은 출처의 리소스만 로드 허용
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # 리퍼러 정책: 같은 출처에는 전체 URL 전송,
        # 다른 출처에는 출처(origin)만 전송
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 권한 정책: 카메라, 마이크, 위치 정보 접근 차단
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        return response


# ============================================================
# API Key 인증 의존성
# ============================================================

# X-API-Key 헤더에서 API 키를 추출하는 보안 스킴
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    api_key: Annotated[str | None, Depends(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    """
    API Key를 검증하는 의존성 함수.
    설정에 정의된 API_KEY와 요청 헤더의 값을 비교한다.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key가 제공되지 않았습니다. X-API-Key 헤더를 확인하세요.",
        )
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 API Key입니다.",
        )
    return api_key


# ============================================================
# FastAPI 앱 생성 및 미들웨어 등록
# ============================================================

# 앱 시작 시 설정 로드
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="보안 강화 예제: Rate Limiting, 보안 헤더, CORS, 환경변수 관리",
    version="1.0.0",
    debug=settings.DEBUG,
)

# 보안 헤더 미들웨어 등록 (모든 응답에 보안 헤더 추가)
app.add_middleware(SecurityHeadersMiddleware)

# CORS 미들웨어 등록 (허용된 출처에서만 API 접근 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,   # 허용할 출처 목록
    allow_credentials=True,                   # 쿠키/인증 정보 포함 허용
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 허용할 HTTP 메서드
    allow_headers=["*"],                      # 허용할 요청 헤더
    expose_headers=["X-Request-ID"],          # 클라이언트에 노출할 응답 헤더
)


# ============================================================
# 엔드포인트: 공개 (인증 불필요)
# ============================================================

@app.get("/", tags=["공개"])
async def root():
    """루트 엔드포인트: 사용 가능한 API 목록 반환"""
    return {
        "message": f"{settings.APP_NAME}에 오신 것을 환영합니다",
        "endpoints": {
            "공개": "/",
            "헬스체크": "/health",
            "속도 제한 테스트": "/limited",
            "설정 정보": "/settings/info",
            "보호된 데이터": "/protected/data (X-API-Key 필요)",
            "보호된 작업": "POST /protected/action (X-API-Key + Rate Limit)",
        },
    }


@app.get("/health", tags=["공개"])
async def health_check():
    """서버 상태 확인 엔드포인트"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "debug_mode": settings.DEBUG,
    }


# ============================================================
# 엔드포인트: Rate Limiting 테스트
# ============================================================

@app.get("/limited", tags=["Rate Limiting"], dependencies=[Depends(rate_limit)])
async def rate_limited_endpoint():
    """
    Rate Limiting이 적용된 엔드포인트.
    설정된 시간 창 내에 최대 요청 횟수를 초과하면 429 에러가 반환된다.
    """
    return {
        "message": "요청이 정상적으로 처리되었습니다",
        "rate_limit_info": {
            "max_requests": settings.RATE_LIMIT_REQUESTS,
            "window_seconds": settings.RATE_LIMIT_WINDOW_SECONDS,
        },
    }


@app.get(
    "/limited/data",
    tags=["Rate Limiting"],
    dependencies=[Depends(rate_limit)],
)
async def rate_limited_data():
    """Rate Limiting이 적용된 데이터 조회 엔드포인트"""
    return {
        "data": [
            {"id": 1, "name": "항목 A", "value": 100},
            {"id": 2, "name": "항목 B", "value": 200},
            {"id": 3, "name": "항목 C", "value": 300},
        ],
    }


# ============================================================
# 엔드포인트: 설정 정보 (민감 정보 마스킹)
# ============================================================

@app.get("/settings/info", tags=["설정"])
async def settings_info(
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    현재 애플리케이션 설정을 반환하는 엔드포인트.
    민감한 정보(SECRET_KEY, API_KEY, DATABASE_URL)는 마스킹하여 노출을 방지한다.
    """

    def mask_value(value: str) -> str:
        """값의 처음 4자만 보여주고 나머지는 마스킹"""
        if len(value) <= 4:
            return "****"
        return value[:4] + "*" * (len(value) - 4)

    return {
        "app_name": settings.APP_NAME,
        "debug": settings.DEBUG,
        "secret_key": mask_value(settings.SECRET_KEY),
        "database_url": mask_value(settings.DATABASE_URL),
        "api_key": mask_value(settings.API_KEY),
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "rate_limit": {
            "max_requests": settings.RATE_LIMIT_REQUESTS,
            "window_seconds": settings.RATE_LIMIT_WINDOW_SECONDS,
        },
    }


# ============================================================
# 엔드포인트: API Key로 보호된 엔드포인트
# ============================================================

@app.get("/protected/data", tags=["보호된 엔드포인트"])
async def get_protected_data(
    api_key: Annotated[str, Depends(verify_api_key)],
):
    """
    API Key 인증이 필요한 데이터 조회 엔드포인트.
    X-API-Key 헤더에 유효한 키를 포함해야 접근 가능하다.
    """
    return {
        "message": "인증된 요청으로 보호된 데이터에 접근했습니다",
        "data": {
            "secret_items": [
                {"id": 1, "content": "비밀 데이터 A"},
                {"id": 2, "content": "비밀 데이터 B"},
            ],
        },
    }


@app.post("/protected/action", tags=["보호된 엔드포인트"])
async def protected_action(
    api_key: Annotated[str, Depends(verify_api_key)],
    _: Annotated[None, Depends(rate_limit)],
    action: str = "default",
):
    """
    API Key 인증과 Rate Limiting이 동시에 적용된 엔드포인트.
    두 가지 보안 계층을 조합하여 더 강력한 보호를 구현한다.
    """
    return {
        "message": "보호된 작업이 실행되었습니다",
        "action": action,
        "status": "completed",
    }


# ============================================================
# 엔드포인트: CORS 테스트용
# ============================================================

@app.get("/cors/test", tags=["CORS"])
async def cors_test():
    """
    CORS 테스트용 엔드포인트.
    브라우저에서 다른 출처로부터의 요청이 허용/차단되는지 확인할 수 있다.
    """
    return {
        "message": "CORS 테스트 응답",
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "note": "브라우저 개발자 도구에서 다른 출처의 fetch() 요청으로 테스트하세요",
    }


@app.options("/cors/test", tags=["CORS"])
async def cors_preflight():
    """CORS Preflight 요청 처리 (CORSMiddleware가 자동 처리하지만 참고용)"""
    return JSONResponse(
        content={"message": "CORS preflight 요청입니다"},
        headers={
            "Access-Control-Allow-Origin": ", ".join(settings.ALLOWED_ORIGINS),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
            "Access-Control-Allow-Headers": "*",
        },
    )


# ============================================================
# 엔드포인트: 보안 정보
# ============================================================

@app.get("/security/headers-info", tags=["보안 정보"])
async def security_headers_info():
    """
    현재 적용된 보안 헤더 목록과 각 헤더의 역할을 설명하는 엔드포인트.
    응답 자체에도 SecurityHeadersMiddleware에 의해 보안 헤더가 포함된다.
    """
    return {
        "message": "이 응답의 헤더를 확인하세요 (curl -I 사용 권장)",
        "security_headers": {
            "X-Content-Type-Options": {
                "value": "nosniff",
                "description": "MIME 타입 스니핑 공격을 방지합니다",
            },
            "X-Frame-Options": {
                "value": "DENY",
                "description": "클릭재킹(iframe 삽입)을 차단합니다",
            },
            "X-XSS-Protection": {
                "value": "1; mode=block",
                "description": "브라우저의 내장 XSS 필터를 활성화합니다",
            },
            "Strict-Transport-Security": {
                "value": "max-age=31536000; includeSubDomains",
                "description": "HTTPS 접속을 강제합니다 (HSTS)",
            },
            "Content-Security-Policy": {
                "value": "default-src 'self'",
                "description": "같은 출처의 리소스만 로드를 허용합니다",
            },
            "Referrer-Policy": {
                "value": "strict-origin-when-cross-origin",
                "description": "리퍼러 정보 전송을 제어합니다",
            },
            "Permissions-Policy": {
                "value": "camera=(), microphone=(), geolocation=()",
                "description": "브라우저 기능(카메라, 마이크 등) 접근을 차단합니다",
            },
        },
    }
