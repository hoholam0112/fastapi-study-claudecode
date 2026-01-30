"""
API v1 라우터 모듈

v1 버전의 모든 엔드포인트를 통합하는 라우터입니다.
"""

from fastapi import APIRouter

# TODO: APIRouter 인스턴스를 생성하세요
#   - prefix="/api/v1"을 설정하세요
#   - (참고: Phase 1 - APIRouter, 라우팅)

router = APIRouter(prefix="/api/v1")

# TODO: 각 엔드포인트 모듈의 라우터를 포함(include)하세요
#   - inference 엔드포인트 라우터를 포함하세요
#   - auth 엔드포인트 라우터를 포함하세요
#   - 적절한 tags를 설정하여 API 문서를 구성하세요
