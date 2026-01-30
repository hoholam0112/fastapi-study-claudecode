"""
Chapter 09: 미들웨어 (Middleware)

미들웨어의 개념, CORS 설정, 커스텀 미들웨어 작성법을 학습한다.
데코레이터 방식과 BaseHTTPMiddleware 클래스 방식 모두 다룬다.

실행 방법:
    uvicorn main:app --reload
"""

import time
import uuid
import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ============================================================
# 로깅 설정
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================
# FastAPI 앱 생성
# ============================================================
app = FastAPI(
    title="Chapter 09: 미들웨어",
    description="미들웨어 개념, CORS, 커스텀 미들웨어 학습",
    version="1.0.0",
)


# ============================================================
# 1. BaseHTTPMiddleware 클래스 방식 - 요청 로깅 미들웨어
# ============================================================
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    요청 로깅 미들웨어 (BaseHTTPMiddleware 클래스 방식)

    모든 요청에 대해 HTTP 메서드, URL, 처리 시간을 로깅한다.
    클래스 방식은 복잡한 로직이나 초기화 파라미터가 필요할 때 적합하다.
    """

    def __init__(self, app, app_name: str = "FastAPI"):
        super().__init__(app)
        # 초기화 시 파라미터를 받을 수 있다 (클래스 방식의 장점)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # --- 요청 전처리 ---
        start_time = time.perf_counter()
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        logger.info(
            f"[{self.app_name}] 요청 시작: {method} {url} (클라이언트: {client_host})"
        )

        # 다음 미들웨어 또는 엔드포인트 호출
        response = await call_next(request)

        # --- 응답 후처리 ---
        process_time = time.perf_counter() - start_time
        status_code = response.status_code

        logger.info(
            f"[{self.app_name}] 요청 완료: {method} {url} "
            f"- 상태: {status_code} - 처리 시간: {process_time:.4f}초"
        )

        return response


# ============================================================
# 2. BaseHTTPMiddleware 클래스 방식 - 커스텀 헤더 추가 미들웨어
# ============================================================
class CustomHeaderMiddleware(BaseHTTPMiddleware):
    """
    커스텀 헤더 추가 미들웨어 (BaseHTTPMiddleware 클래스 방식)

    모든 응답에 X-Request-ID 헤더를 추가하여 요청 추적을 가능하게 한다.
    분산 시스템에서 로그 추적에 매우 유용한 패턴이다.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 고유한 요청 ID 생성 (UUID4 사용)
        request_id = str(uuid.uuid4())

        # 요청 상태(state)에 request_id를 저장하여 엔드포인트에서도 접근 가능하게 한다
        request.state.request_id = request_id

        logger.info(f"[CustomHeader] 요청 ID 할당: {request_id}")

        # 다음 미들웨어 또는 엔드포인트 호출
        response = await call_next(request)

        # 응답 헤더에 요청 ID 추가
        response.headers["X-Request-ID"] = request_id
        # 서버 정보 헤더 추가
        response.headers["X-Powered-By"] = "FastAPI Study"

        return response


# ============================================================
# 3. @app.middleware("http") 데코레이터 방식 - 처리 시간 측정 미들웨어
# ============================================================
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable) -> Response:
    """
    요청 처리 시간 측정 미들웨어 (데코레이터 방식)

    모든 응답에 X-Process-Time 헤더를 추가한다.
    데코레이터 방식은 간단한 미들웨어를 빠르게 작성할 때 적합하다.

    주의: @app.middleware로 등록한 미들웨어는 app.add_middleware()보다
    먼저 실행된다 (엔드포인트에 더 가까움).
    """
    # 요청 처리 시작 시간 기록
    start_time = time.perf_counter()

    # 다음 미들웨어 또는 엔드포인트 호출
    response = await call_next(request)

    # 처리 시간 계산 (초 단위, 소수점 6자리)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response


# ============================================================
# 4. @app.middleware("http") 데코레이터 방식 - 실행 순서 확인 미들웨어
# ============================================================
@app.middleware("http")
async def middleware_order_demo(request: Request, call_next: Callable) -> Response:
    """
    미들웨어 실행 순서를 확인하기 위한 데모 미들웨어 (데코레이터 방식)

    @app.middleware 데코레이터는 코드 상 위에 있는 것이 나중에 실행된다.
    즉, 이 미들웨어가 add_process_time_header보다 먼저 실행된다.
    """
    logger.info("[순서확인] 데코레이터 미들웨어 B - 요청 진입")

    response = await call_next(request)

    logger.info("[순서확인] 데코레이터 미들웨어 B - 응답 반환")
    return response


# ============================================================
# 5. CORS 미들웨어 설정
# ============================================================
# 허용할 출처(origin) 목록 정의
# 실무에서는 환경 변수로 관리하는 것이 좋다
ALLOWED_ORIGINS = [
    "http://localhost:3000",     # React 개발 서버
    "http://localhost:5173",     # Vite 개발 서버
    "http://localhost:8080",     # Vue 개발 서버
    "http://127.0.0.1:5500",    # VS Code Live Server
]

app.add_middleware(
    CORSMiddleware,
    # 허용할 출처 목록 (["*"]는 모든 출처 허용, 개발 시에만 사용 권장)
    allow_origins=ALLOWED_ORIGINS,
    # 쿠키 및 인증 정보 포함 허용 여부
    allow_credentials=True,
    # 허용할 HTTP 메서드 (["*"]는 모든 메서드 허용)
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    # 허용할 요청 헤더
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    # 브라우저에 노출할 응답 헤더 (기본적으로 CORS는 응답 헤더를 숨긴다)
    expose_headers=["X-Process-Time", "X-Request-ID"],
    # preflight 요청 캐시 시간 (초) - 600초 = 10분
    max_age=600,
)

# ============================================================
# 6. BaseHTTPMiddleware 클래스 방식 미들웨어 등록
# ============================================================
# add_middleware의 등록 순서: 나중에 등록한 것이 요청을 먼저 처리한다.
# 즉, CustomHeaderMiddleware가 RequestLoggingMiddleware보다 먼저 실행된다.
app.add_middleware(RequestLoggingMiddleware, app_name="미들웨어학습")
app.add_middleware(CustomHeaderMiddleware)


# ============================================================
# 테스트용 엔드포인트들
# ============================================================

@app.get("/", summary="루트 엔드포인트")
async def root():
    """
    기본 루트 엔드포인트.
    응답 헤더에서 X-Process-Time, X-Request-ID를 확인할 수 있다.
    """
    return {
        "message": "Chapter 09: 미들웨어 학습",
        "description": "응답 헤더에서 X-Process-Time과 X-Request-ID를 확인해보세요.",
    }


@app.get("/items", summary="아이템 목록 조회")
async def get_items():
    """
    샘플 아이템 목록을 반환한다.
    CORS 테스트 시 다른 출처에서 이 엔드포인트를 호출해본다.
    """
    items = [
        {"id": 1, "name": "노트북", "price": 1500000},
        {"id": 2, "name": "키보드", "price": 120000},
        {"id": 3, "name": "마우스", "price": 80000},
    ]
    return {"items": items, "total": len(items)}


@app.get("/items/{item_id}", summary="아이템 상세 조회")
async def get_item(item_id: int):
    """
    특정 아이템의 상세 정보를 반환한다.
    존재하지 않는 ID를 요청하면 404 에러를 반환한다.
    """
    # 샘플 데이터
    sample_items = {
        1: {"id": 1, "name": "노트북", "price": 1500000, "category": "전자기기"},
        2: {"id": 2, "name": "키보드", "price": 120000, "category": "주변기기"},
        3: {"id": 3, "name": "마우스", "price": 80000, "category": "주변기기"},
    }

    item = sample_items.get(item_id)
    if not item:
        return JSONResponse(
            status_code=404,
            content={"detail": f"아이템 ID {item_id}을(를) 찾을 수 없습니다."},
        )
    return item


@app.get("/slow", summary="지연 응답 테스트")
async def slow_endpoint():
    """
    인위적으로 2초 지연을 발생시키는 엔드포인트.
    X-Process-Time 헤더를 통해 처리 시간 측정을 확인할 수 있다.

    curl -v http://localhost:8000/slow 로 테스트해보자.
    """
    import asyncio

    # 2초간 비동기 대기 (블로킹하지 않음)
    await asyncio.sleep(2)
    return {
        "message": "이 응답은 2초 후에 반환됩니다.",
        "tip": "응답 헤더의 X-Process-Time 값을 확인해보세요.",
    }


@app.get("/middleware-order", summary="미들웨어 실행 순서 확인")
async def middleware_order():
    """
    미들웨어 실행 순서를 확인하기 위한 엔드포인트.
    서버 콘솔 로그를 확인하여 어떤 미들웨어가 먼저 실행되는지 관찰한다.

    실행 순서 (요청 처리):
    1. CustomHeaderMiddleware (add_middleware로 나중에 등록 → 가장 먼저 실행)
    2. RequestLoggingMiddleware (add_middleware로 먼저 등록)
    3. middleware_order_demo (데코레이터 방식, 코드 상 아래)
    4. add_process_time_header (데코레이터 방식, 코드 상 위 → 엔드포인트에 가장 가까움)
    5. 이 엔드포인트 함수
    """
    logger.info("[엔드포인트] middleware-order 핸들러 실행")
    return {
        "message": "서버 콘솔 로그에서 미들웨어 실행 순서를 확인하세요.",
        "expected_order": [
            "1. CustomHeaderMiddleware (요청 진입)",
            "2. RequestLoggingMiddleware (요청 시작 로그)",
            "3. 데코레이터 미들웨어 B (요청 진입)",
            "4. 처리 시간 측정 미들웨어 (시작)",
            "5. 엔드포인트 핸들러 실행",
            "6. 처리 시간 측정 미들웨어 (완료, 헤더 추가)",
            "7. 데코레이터 미들웨어 B (응답 반환)",
            "8. RequestLoggingMiddleware (요청 완료 로그)",
            "9. CustomHeaderMiddleware (헤더 추가)",
        ],
    }


@app.get("/request-info", summary="요청 정보 확인")
async def request_info(request: Request):
    """
    현재 요청의 상세 정보를 반환한다.
    미들웨어에서 설정한 request.state 값도 확인할 수 있다.
    """
    # CustomHeaderMiddleware에서 설정한 request_id 가져오기
    request_id = getattr(request.state, "request_id", "설정되지 않음")

    return {
        "method": request.method,
        "url": str(request.url),
        "base_url": str(request.base_url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "client": {
            "host": request.client.host if request.client else None,
            "port": request.client.port if request.client else None,
        },
        "request_id_from_middleware": request_id,
    }


@app.get("/health", summary="헬스 체크")
async def health_check():
    """
    서버 상태 확인용 헬스 체크 엔드포인트.
    모니터링 시스템에서 주기적으로 호출하는 용도로 사용한다.
    """
    return {"status": "healthy", "service": "ch09_middleware"}
