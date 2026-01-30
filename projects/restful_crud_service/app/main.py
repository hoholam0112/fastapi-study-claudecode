"""
RESTful CRUD 서비스 - 메인 애플리케이션

이 파일은 FastAPI 애플리케이션의 진입점입니다.
모든 Phase를 학습한 후 아래 TODO 항목들을 구현해 보세요.
"""

from fastapi import FastAPI

# TODO: FastAPI 앱 인스턴스를 생성하세요
#   - title, description, version 등 메타데이터를 설정하세요
#   - (참고: Phase 1 - FastAPI 기초)

app = FastAPI(
    title="RESTful CRUD 서비스",
    description="게시판/블로그 REST API",
    version="0.1.0",
)


# TODO: 데이터베이스 테이블 생성 및 lifespan 이벤트를 구현하세요
#   - startup 이벤트에서 DB 연결을 초기화하세요
#   - shutdown 이벤트에서 DB 연결을 종료하세요
#   - (참고: Phase 2 - 데이터베이스 연동, Phase 3 - 비동기 프로그래밍)


# TODO: API 라우터를 포함(include)하세요
#   - /api/v1/auth 접두사로 인증 라우터를 등록하세요
#   - /api/v1/posts 접두사로 게시글 라우터를 등록하세요
#   - /api/v1/comments 접두사로 댓글 라우터를 등록하세요 (선택)
#   - (참고: Phase 1 - APIRouter, 라우팅)


# TODO: 미들웨어를 설정하세요
#   - CORS 미들웨어를 추가하세요
#   - 요청 로깅 미들웨어를 추가하세요 (선택)
#   - (참고: Phase 3 - 미들웨어)


# TODO: 전역 예외 핸들러를 등록하세요
#   - (참고: Phase 3 - 에러 핸들링)


# TODO: 헬스 체크 엔드포인트를 구현하세요
@app.get("/health")
async def health_check():
    # TODO: DB 연결 상태 등을 포함한 헬스 체크 로직을 구현하세요
    return {"status": "ok"}
