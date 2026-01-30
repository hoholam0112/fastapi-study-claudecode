"""
API v1 라우터 통합 모듈

v1 버전의 모든 엔드포인트 라우터를 하나로 결합한다.
새로운 리소스 엔드포인트를 추가할 때 이 파일에 include_router()를 추가하면 된다.

구조:
    api_router (이 모듈)
    ├── users (endpoints/users.py)
    └── items (endpoints/items.py)

사용법:
    main.py에서 이 api_router를 "/api/v1" 접두사와 함께 포함한다.
    최종 경로 예시: /api/v1/users/, /api/v1/items/
"""

from fastapi import APIRouter

# 각 엔드포인트 모듈에서 라우터를 가져온다
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.items import router as items_router

# v1 API의 최상위 라우터를 생성한다
# 이 라우터에 모든 v1 엔드포인트 라우터를 결합한다
api_router = APIRouter()

# 사용자 엔드포인트 포함 (/users/*)
api_router.include_router(users_router)

# 아이템 엔드포인트 포함 (/items/*)
api_router.include_router(items_router)

# 새로운 리소스를 추가하려면 아래와 같이 라우터를 포함한다:
# from app.api.v1.endpoints.products import router as products_router
# api_router.include_router(products_router)
