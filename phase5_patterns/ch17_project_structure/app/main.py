"""
FastAPI 애플리케이션 진입점 (Entry Point)

이 모듈은 FastAPI 앱 인스턴스를 생성하고,
모든 라우터를 결합하며, 애플리케이션 수명 주기를 관리한다.

실행 방법:
    ch17_project_structure 디렉토리에서 아래 명령어를 실행한다:
    $ uvicorn app.main:app --reload

    또는 포트를 지정하여 실행한다:
    $ uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.api.v1.router import api_router

# 로거 설정
logger = logging.getLogger(__name__)

# 설정 객체를 가져온다 (lru_cache로 캐싱됨)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 수명 주기 관리자 (lifespan)

    앱 시작 시와 종료 시 실행할 코드를 정의한다.
    FastAPI 0.93+ 버전에서 권장하는 방식이다.

    - yield 이전: 앱 시작 시 실행 (데이터베이스 연결, 캐시 초기화 등)
    - yield 이후: 앱 종료 시 실행 (리소스 정리, 연결 해제 등)
    """
    # ── 시작 시 실행되는 코드 ──
    logger.info("애플리케이션 시작: %s v%s", settings.APP_NAME, settings.VERSION)
    logger.info("디버그 모드: %s", settings.DEBUG)
    logger.info("데이터베이스 URL: %s", settings.DATABASE_URL)

    # 실제 프로젝트에서는 여기서 다음 작업을 수행한다:
    # - 데이터베이스 연결 풀 초기화
    # - Redis 캐시 연결
    # - 백그라운드 작업 스케줄러 시작
    # - ML 모델 로드 등

    yield  # 이 지점에서 앱이 요청을 처리한다

    # ── 종료 시 실행되는 코드 ──
    logger.info("애플리케이션 종료: 리소스를 정리합니다.")

    # 실제 프로젝트에서는 여기서 다음 작업을 수행한다:
    # - 데이터베이스 연결 해제
    # - 캐시 연결 해제
    # - 임시 파일 정리 등


# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=(
        "FastAPI 프로젝트 구조 설계 학습용 데모 애플리케이션입니다.\n\n"
        "이 프로젝트는 다음 개념을 다룹니다:\n"
        "- APIRouter를 활용한 엔드포인트 모듈 분리\n"
        "- 계층 분리 패턴 (Router -> CRUD -> Model)\n"
        "- BaseSettings를 사용한 환경 설정 관리\n"
        "- Pydantic 스키마를 활용한 데이터 검증"
    ),
    lifespan=lifespan,
    # Swagger UI 설정
    docs_url="/docs",
    redoc_url="/redoc",
)

# v1 API 라우터를 앱에 포함한다
# prefix="/api/v1"을 지정하여 모든 v1 엔드포인트에 공통 경로 접두사를 부여한다
# 최종 경로 예시: /api/v1/users/, /api/v1/items/
app.include_router(api_router, prefix="/api/v1")


@app.get(
    "/",
    tags=["root"],
    summary="루트 엔드포인트",
    description="앱의 기본 정보를 반환하는 헬스체크 겸 루트 엔드포인트이다.",
)
async def root():
    """
    루트 엔드포인트

    애플리케이션의 기본 정보와 상태를 반환한다.
    헬스체크 용도로도 사용할 수 있다.
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        "message": "FastAPI 프로젝트 구조 데모에 오신 것을 환영합니다!",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["root"],
    summary="헬스체크",
    description="애플리케이션의 상태를 확인하는 엔드포인트이다.",
)
async def health_check():
    """
    헬스체크 엔드포인트

    로드밸런서나 모니터링 시스템에서 앱의 상태를 확인할 때 사용한다.
    """
    return {"status": "healthy"}
