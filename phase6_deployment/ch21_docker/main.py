"""
Chapter 21: Docker를 활용한 FastAPI 배포
========================================
Docker 컨테이너 환경에서 실행되는 FastAPI 애플리케이션 예제.
환경변수를 통해 설정을 주입받고, 헬스체크 및 정보 엔드포인트를 제공한다.

실행 방법:
    uvicorn main:app --reload
"""

import os
import platform
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

# ============================================================
# 환경변수에서 설정 읽기 (기본값 포함)
# Docker 실행 시 -e 옵션이나 docker-compose의 environment로 주입한다
# ============================================================
APP_NAME: str = os.getenv("APP_NAME", "FastAPI Docker 학습")
VERSION: str = os.getenv("VERSION", "1.0.0")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

# ============================================================
# FastAPI 애플리케이션 인스턴스 생성
# ============================================================
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Docker 컨테이너 환경에서 동작하는 FastAPI 학습용 애플리케이션",
)

# 서버 시작 시각을 기록하여 가동 시간 계산에 활용한다
SERVER_START_TIME: datetime = datetime.now(timezone.utc)


# ============================================================
# 응답 모델 정의
# Pydantic 모델을 사용하여 API 응답의 구조를 명확히 한다
# ============================================================
class HealthResponse(BaseModel):
    """헬스체크 응답 모델"""

    status: str
    timestamp: str


class InfoResponse(BaseModel):
    """애플리케이션 정보 응답 모델"""

    app_name: str
    version: str
    environment: str
    debug: bool
    python_version: str
    platform: str
    server_start_time: str
    uptime_seconds: float


class WelcomeResponse(BaseModel):
    """환영 메시지 응답 모델"""

    message: str
    docs_url: str


# ============================================================
# 라이프사이클 이벤트
# 애플리케이션 시작/종료 시 실행되는 로직을 정의한다
# ============================================================
@app.on_event("startup")
async def on_startup() -> None:
    """애플리케이션 시작 시 초기화 작업을 수행한다."""
    print(f"[시작] {APP_NAME} v{VERSION} ({ENVIRONMENT} 환경)")
    print(f"[시작] 디버그 모드: {DEBUG}")
    print(f"[시작] Python {platform.python_version()} / {platform.system()} {platform.release()}")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """애플리케이션 종료 시 정리 작업을 수행한다."""
    print(f"[종료] {APP_NAME} 서버를 종료합니다.")


# ============================================================
# API 엔드포인트
# ============================================================
@app.get(
    "/",
    response_model=WelcomeResponse,
    summary="환영 메시지",
    description="루트 경로에 접속하면 환영 메시지와 API 문서 경로를 반환한다.",
)
async def root() -> WelcomeResponse:
    """루트 엔드포인트: 환영 메시지를 반환한다."""
    return WelcomeResponse(
        message=f"{APP_NAME}에 오신 것을 환영합니다! (v{VERSION})",
        docs_url="/docs",
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="헬스체크",
    description="서비스 상태를 확인하는 헬스체크 엔드포인트. 로드밸런서나 Docker HEALTHCHECK에서 사용한다.",
)
async def health_check() -> HealthResponse:
    """
    헬스체크 엔드포인트.
    Docker의 HEALTHCHECK 또는 쿠버네티스의 livenessProbe에서 호출한다.
    정상 동작 시 {"status": "healthy"}를 반환한다.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get(
    "/info",
    response_model=InfoResponse,
    summary="애플리케이션 정보",
    description="애플리케이션 이름, 버전, 실행 환경 등 상세 정보를 반환한다.",
)
async def app_info() -> InfoResponse:
    """
    애플리케이션 정보 엔드포인트.
    환경변수로 주입된 설정값과 시스템 정보를 반환한다.
    배포 환경을 검증하거나 디버깅할 때 유용하다.
    """
    # 현재 시각과 서버 시작 시각의 차이로 가동 시간을 계산한다
    now = datetime.now(timezone.utc)
    uptime = (now - SERVER_START_TIME).total_seconds()

    return InfoResponse(
        app_name=APP_NAME,
        version=VERSION,
        environment=ENVIRONMENT,
        debug=DEBUG,
        python_version=platform.python_version(),
        platform=f"{platform.system()} {platform.release()}",
        server_start_time=SERVER_START_TIME.isoformat(),
        uptime_seconds=round(uptime, 2),
    )
