"""
ML 모델 서빙 API - 메인 애플리케이션

이 파일은 FastAPI 애플리케이션의 진입점입니다.
모든 Phase를 학습한 후 아래 TODO 항목들을 구현해 보세요.
"""

from fastapi import FastAPI

# TODO: FastAPI 앱 인스턴스를 생성하세요
#   - title, description, version 등 메타데이터를 설정하세요
#   - (참고: Phase 1 - FastAPI 기초)

app = FastAPI(
    title="ML 모델 서빙 API",
    description="머신러닝 모델 추론 서비스",
    version="0.1.0",
)


# TODO: 앱 시작 시 ML 모델을 로드하는 lifespan 이벤트를 구현하세요
#   - startup 이벤트에서 모델을 미리 로드합니다
#   - shutdown 이벤트에서 리소스를 정리합니다
#   - (참고: Phase 3 - 비동기 프로그래밍, 미들웨어)


# TODO: API v1 라우터를 포함(include)하세요
#   - /api/v1 접두사로 추론 관련 엔드포인트를 등록하세요
#   - /auth 접두사로 인증 관련 엔드포인트를 등록하세요
#   - (참고: Phase 1 - 라우팅, APIRouter)


# TODO: 헬스 체크 엔드포인트를 구현하세요
#   - GET /health 경로로 서비스 상태를 반환하세요
#   - 모델 로딩 상태도 함께 반환하면 좋습니다
@app.get("/health")
async def health_check():
    # TODO: 실제 헬스 체크 로직을 구현하세요
    return {"status": "ok"}
