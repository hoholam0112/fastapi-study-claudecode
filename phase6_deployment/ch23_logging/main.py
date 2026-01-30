"""
Chapter 23: 로깅과 모니터링

Python logging 모듈, 구조화 로깅(JSON), 요청 로깅 미들웨어,
Health Check 엔드포인트 패턴을 학습한다.

실행 방법:
    pip install fastapi uvicorn python-json-logger
    uvicorn main:app --reload
"""

import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# ============================================================
# 1. 기본 로거 설정 (StreamHandler + Formatter)
# ============================================================

# 기본 텍스트 포맷 로거 생성
text_logger = logging.getLogger("app.text")
text_logger.setLevel(logging.DEBUG)  # 로거 자체는 DEBUG까지 허용

# 콘솔 출력 핸들러 생성
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)

# 포맷터 설정: 시간, 로거 이름, 레벨, 메시지를 포함
text_formatter = logging.Formatter(
    fmt="%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
stream_handler.setFormatter(text_formatter)
text_logger.addHandler(stream_handler)

# ============================================================
# 2. JSON 포맷 구조화 로거 설정 (python-json-logger)
# ============================================================

# python-json-logger 임포트 (구조화 로깅을 위한 외부 라이브러리)
try:
    from pythonjsonlogger import json as jsonlogger

    # JSON 로거 생성
    json_logger = logging.getLogger("app.json")
    json_logger.setLevel(logging.DEBUG)

    # JSON 포맷 핸들러 설정
    json_handler = logging.StreamHandler()
    json_handler.setLevel(logging.INFO)

    # JSON 포맷터: 타임스탬프, 레벨, 메시지 등을 JSON 구조로 출력
    json_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    json_handler.setFormatter(json_formatter)
    json_logger.addHandler(json_handler)

    JSON_LOGGING_AVAILABLE = True
    text_logger.info("JSON 로깅 활성화됨 (python-json-logger 사용)")
except ImportError:
    # python-json-logger가 설치되지 않은 경우 텍스트 로거로 대체
    json_logger = text_logger
    JSON_LOGGING_AVAILABLE = False
    text_logger.warning(
        "python-json-logger가 설치되지 않음. "
        "텍스트 로거로 대체합니다. "
        "설치: pip install python-json-logger"
    )

# ============================================================
# 3. FastAPI 애플리케이션 설정
# ============================================================

app = FastAPI(
    title="Chapter 23: 로깅과 모니터링",
    description="Python logging, 구조화 로깅, Health Check 패턴 학습",
    version="1.0.0",
)

# 애플리케이션 시작 시간 기록 (Health Check에서 uptime 계산에 사용)
APP_START_TIME = datetime.now(timezone.utc)
APP_VERSION = "1.0.0"


# ============================================================
# 4. 요청 로깅 미들웨어
# ============================================================


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:
    """
    모든 HTTP 요청/응답을 자동으로 로깅하는 미들웨어.

    기록 항목:
    - request_id: 각 요청의 고유 식별자 (UUID)
    - method: HTTP 메서드 (GET, POST 등)
    - path: 요청 경로
    - status_code: 응답 상태 코드
    - duration_ms: 요청 처리 소요 시간 (밀리초)
    """
    # 요청마다 고유 ID를 부여하여 추적 가능하게 만든다
    request_id = str(uuid.uuid4())[:8]

    # 요청 처리 시작 시간 기록
    start_time = time.perf_counter()

    # 요청 수신 로그 (텍스트 로거)
    text_logger.info(
        f"[{request_id}] 요청 수신: {request.method} {request.url.path}"
    )

    # 다음 미들웨어 또는 엔드포인트로 요청 전달
    response = await call_next(request)

    # 처리 시간 계산 (밀리초 단위)
    duration_ms = (time.perf_counter() - start_time) * 1000

    # JSON 구조화 로그 출력 (검색 및 분석에 유리)
    json_logger.info(
        "요청 처리 완료",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_host": request.client.host if request.client else "unknown",
        },
    )

    # 응답 헤더에 요청 ID를 포함시켜 클라이언트도 추적 가능하게 한다
    response.headers["X-Request-ID"] = request_id
    # 처리 시간도 헤더에 포함
    response.headers["X-Process-Time-Ms"] = str(round(duration_ms, 2))

    return response


# ============================================================
# 5. Health Check 엔드포인트
# ============================================================


@app.get(
    "/health",
    tags=["Health Check"],
    summary="기본 서비스 상태 확인",
    description="서비스가 정상 동작 중인지 확인하는 liveness 엔드포인트",
)
async def health_check():
    """
    기본 Health Check (Liveness Probe).

    Kubernetes나 로드밸런서에서 주기적으로 호출하여
    서비스가 살아있는지 확인하는 용도로 사용한다.

    반환값:
    - status: 서비스 상태 ("healthy")
    - timestamp: 현재 UTC 시간
    - version: 애플리케이션 버전
    - uptime_seconds: 서비스 가동 시간 (초)
    """
    now = datetime.now(timezone.utc)
    uptime = (now - APP_START_TIME).total_seconds()

    text_logger.info("Health Check 요청 처리됨")

    return {
        "status": "healthy",
        "timestamp": now.isoformat(),
        "version": APP_VERSION,
        "uptime_seconds": round(uptime, 1),
    }


@app.get(
    "/health/db",
    tags=["Health Check"],
    summary="데이터베이스 연결 상태 확인",
    description="데이터베이스 연결이 정상인지 확인하는 readiness 엔드포인트",
)
async def health_check_db():
    """
    DB Health Check (Readiness Probe).

    데이터베이스 연결 상태를 확인하여 서비스가 트래픽을
    처리할 준비가 되었는지 판단한다.

    실제 운영에서는 DB에 간단한 쿼리(SELECT 1)를 실행하여
    연결 상태를 확인한다.
    """
    try:
        # --- DB 연결 체크 시뮬레이션 ---
        # 실제 환경에서는 아래와 같이 DB 쿼리를 실행한다:
        #   async with db.acquire() as conn:
        #       await conn.execute("SELECT 1")
        db_connected = True
        db_latency_ms = 2.5  # 시뮬레이션된 DB 응답 시간

        if db_connected:
            json_logger.info(
                "DB Health Check 성공",
                extra={"db_latency_ms": db_latency_ms},
            )
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "latency_ms": db_latency_ms,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            raise ConnectionError("DB 연결 실패")

    except Exception as e:
        # DB 연결 실패 시 503 반환 (서비스 이용 불가 상태)
        json_logger.error(
            "DB Health Check 실패",
            extra={"error": str(e)},
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": {
                    "connected": False,
                    "error": str(e),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


# ============================================================
# 6. 다양한 로그 레벨 시연 엔드포인트
# ============================================================


@app.get(
    "/log/info",
    tags=["로그 레벨 예시"],
    summary="INFO 레벨 로그 시연",
)
async def log_info_example():
    """
    INFO 레벨 로그 예시.

    정상적인 비즈니스 로직 수행 결과를 기록할 때 사용한다.
    예: 사용자 로그인 성공, 주문 생성 완료 등
    """
    # INFO: 정상 동작에 대한 기록
    text_logger.info("사용자가 상품 목록을 조회했습니다")
    json_logger.info(
        "상품 목록 조회",
        extra={
            "action": "product_list_view",
            "user_id": "user_12345",
            "result_count": 42,
        },
    )
    return {
        "level": "INFO",
        "message": "INFO 로그가 기록되었습니다. 터미널 출력을 확인하세요.",
        "description": "정상 동작 확인용 로그입니다.",
    }


@app.get(
    "/log/warning",
    tags=["로그 레벨 예시"],
    summary="WARNING 레벨 로그 시연",
)
async def log_warning_example():
    """
    WARNING 레벨 로그 예시.

    당장 오류는 아니지만 주의가 필요한 상황을 기록할 때 사용한다.
    예: 디스크 사용률 80% 초과, 응답 지연 발생, 인증 토큰 만료 임박 등
    """
    # WARNING: 잠재적 문제 상황 경고
    text_logger.warning("API 응답 시간이 기준치(500ms)를 초과했습니다")
    json_logger.warning(
        "느린 응답 감지",
        extra={
            "action": "slow_response_detected",
            "threshold_ms": 500,
            "actual_ms": 780,
            "endpoint": "/api/v1/products",
        },
    )
    return {
        "level": "WARNING",
        "message": "WARNING 로그가 기록되었습니다. 터미널 출력을 확인하세요.",
        "description": "잠재적 문제 경고용 로그입니다.",
    }


@app.get(
    "/log/error",
    tags=["로그 레벨 예시"],
    summary="ERROR 레벨 로그 시연",
)
async def log_error_example():
    """
    ERROR 레벨 로그 예시.

    실제 오류가 발생했을 때 기록한다.
    예: 외부 API 호출 실패, 데이터 처리 오류, 인증 실패 등
    """
    # ERROR: 오류 발생 기록
    try:
        # 의도적으로 예외를 발생시켜 에러 로깅을 시연
        result = 1 / 0
    except ZeroDivisionError:
        # exc_info=True: 스택 트레이스를 로그에 포함시킨다
        text_logger.error(
            "데이터 처리 중 오류가 발생했습니다",
            exc_info=True,
        )
        json_logger.error(
            "데이터 처리 실패",
            extra={
                "action": "data_processing_error",
                "error_type": "ZeroDivisionError",
                "module": "payment",
                "severity": "high",
            },
        )

    return {
        "level": "ERROR",
        "message": "ERROR 로그가 기록되었습니다. 터미널 출력을 확인하세요.",
        "description": "오류 발생 기록용 로그입니다. 스택 트레이스를 포함합니다.",
    }


@app.get(
    "/log/debug",
    tags=["로그 레벨 예시"],
    summary="DEBUG 레벨 로그 시연",
)
async def log_debug_example():
    """
    DEBUG 레벨 로그 예시.

    개발 중 상세한 디버깅 정보를 기록할 때 사용한다.
    운영 환경에서는 보통 비활성화한다.
    """
    # DEBUG: 개발 중 상세 디버깅 정보
    sample_data = {"user_id": 1, "action": "login", "ip": "192.168.1.100"}
    text_logger.debug(f"요청 데이터 상세: {sample_data}")
    json_logger.debug(
        "디버그 상세 정보",
        extra={
            "action": "debug_trace",
            "raw_data": str(sample_data),
            "step": "request_validation",
        },
    )
    return {
        "level": "DEBUG",
        "message": "DEBUG 로그가 기록되었습니다. 터미널 출력을 확인하세요.",
        "description": "개발용 상세 디버깅 로그입니다. INFO 이상에서는 보이지 않을 수 있습니다.",
    }


# ============================================================
# 7. 루트 엔드포인트
# ============================================================


@app.get(
    "/",
    tags=["기본"],
    summary="루트 엔드포인트",
)
async def root():
    """
    API 루트 엔드포인트.

    사용 가능한 엔드포인트 목록과 간단한 안내를 반환한다.
    """
    text_logger.info("루트 엔드포인트 접근")
    return {
        "message": "Chapter 23: 로깅과 모니터링 학습 API",
        "docs": "/docs",
        "endpoints": {
            "health_check": "/health",
            "health_check_db": "/health/db",
            "log_info": "/log/info",
            "log_warning": "/log/warning",
            "log_error": "/log/error",
            "log_debug": "/log/debug",
        },
        "json_logging_enabled": JSON_LOGGING_AVAILABLE,
    }
