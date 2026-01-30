"""
FastAPI + MongoDB + Redis 연동 애플리케이션

이 모듈은 NoSQL 데이터베이스 활용법을 학습하기 위한 예제입니다.
- MongoDB: motor 비동기 드라이버를 사용한 문서(Document) CRUD
- Redis: 비동기 캐싱 (TTL 기반 자동 만료)

[필수 사전 조건]
- MongoDB가 localhost:27017에서 실행 중이어야 합니다.
- Redis가 localhost:6379에서 실행 중이어야 합니다.

Docker로 간단히 실행:
    docker run -d --name mongodb -p 27017:27017 mongo:7
    docker run -d --name redis -p 6379:6379 redis:7-alpine
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from redis import asyncio as aioredis


# ===========================================================================
# 설정 상수
# ===========================================================================

# MongoDB 연결 설정
MONGODB_URL = "mongodb://localhost:27017"
MONGODB_DB_NAME = "fastapi_nosql_study"  # 데이터베이스 이름
MONGODB_COLLECTION_NAME = "posts"  # 컬렉션 이름 (RDBMS의 테이블에 해당)

# Redis 연결 설정
REDIS_URL = "redis://localhost:6379"
REDIS_CACHE_TTL = 60  # 캐시 유효 시간(초) - 60초 후 자동 만료


# ===========================================================================
# 전역 클라이언트 변수
# ===========================================================================
# 라이프사이클에서 초기화 및 정리됨
mongo_client: AsyncIOMotorClient = None  # type: ignore[assignment]
redis_client: aioredis.Redis = None  # type: ignore[assignment]


# ===========================================================================
# Pydantic 스키마 정의
# ===========================================================================


class PostCreate(BaseModel):
    """게시글 생성 요청 스키마"""

    title: str = Field(..., min_length=1, max_length=200, description="게시글 제목")
    content: str = Field(..., min_length=1, description="게시글 본문")
    author: str = Field(..., min_length=1, max_length=50, description="작성자 이름")
    tags: list[str] = Field(default_factory=list, description="태그 목록")


class PostUpdate(BaseModel):
    """게시글 수정 요청 스키마 - 모든 필드 선택적"""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="게시글 제목")
    content: Optional[str] = Field(None, min_length=1, description="게시글 본문")
    author: Optional[str] = Field(None, min_length=1, max_length=50, description="작성자 이름")
    tags: Optional[list[str]] = Field(None, description="태그 목록")


class PostResponse(BaseModel):
    """게시글 응답 스키마"""

    id: str = Field(..., description="게시글 고유 ID (MongoDB ObjectId)")
    title: str
    content: str
    author: str
    tags: list[str] = []
    created_at: str = Field(..., description="생성 일시 (ISO 8601)")
    updated_at: str = Field(..., description="수정 일시 (ISO 8601)")


class CacheStatusResponse(BaseModel):
    """캐시 상태 응답 스키마"""

    source: str = Field(..., description="데이터 출처 (cache 또는 database)")
    post: PostResponse


# ===========================================================================
# 헬퍼 함수
# ===========================================================================


def _post_document_to_response(doc: dict) -> PostResponse:
    """
    MongoDB 문서(dict)를 PostResponse 스키마로 변환합니다.

    - MongoDB의 _id(ObjectId)를 문자열로 변환
    - datetime 객체를 ISO 8601 문자열로 변환
    """
    return PostResponse(
        id=str(doc["_id"]),
        title=doc["title"],
        content=doc["content"],
        author=doc["author"],
        tags=doc.get("tags", []),
        created_at=doc["created_at"].isoformat() if isinstance(doc["created_at"], datetime) else doc["created_at"],
        updated_at=doc["updated_at"].isoformat() if isinstance(doc["updated_at"], datetime) else doc["updated_at"],
    )


def _get_cache_key(post_id: str) -> str:
    """Redis 캐시 키를 생성합니다."""
    return f"post:{post_id}"


async def _invalidate_cache(post_id: str) -> None:
    """
    특정 게시글의 캐시를 무효화(삭제)합니다.

    데이터가 수정되거나 삭제될 때 호출하여
    캐시와 실제 데이터 간의 일관성을 유지합니다.
    """
    try:
        cache_key = _get_cache_key(post_id)
        await redis_client.delete(cache_key)
    except Exception:
        # Redis 연결 실패 시에도 메인 로직에 영향을 주지 않음
        pass


# ===========================================================================
# 애플리케이션 라이프사이클
# ===========================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 라이프사이클 관리자

    시작 시:
    - MongoDB 클라이언트를 초기화하고 연결을 확인합니다.
    - Redis 클라이언트를 초기화하고 연결을 확인합니다.

    종료 시:
    - MongoDB와 Redis 연결을 정리합니다.
    """
    global mongo_client, redis_client

    # ----- MongoDB 초기화 -----
    mongo_client = AsyncIOMotorClient(MONGODB_URL)

    # 연결 확인 (ping 명령 실행)
    try:
        await mongo_client.admin.command("ping")
        print(f"MongoDB 연결 성공: {MONGODB_URL}")
    except Exception as e:
        print(f"MongoDB 연결 실패: {e}")
        print("MongoDB가 실행 중인지 확인하세요: docker run -d --name mongodb -p 27017:27017 mongo:7")

    # ----- Redis 초기화 -----
    try:
        redis_client = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,  # 응답을 문자열로 자동 디코딩
        )
        await redis_client.ping()
        print(f"Redis 연결 성공: {REDIS_URL}")
    except Exception as e:
        print(f"Redis 연결 실패: {e}")
        print("Redis가 실행 중인지 확인하세요: docker run -d --name redis -p 6379:6379 redis:7-alpine")

    yield  # 애플리케이션 실행 구간

    # ----- 연결 정리 -----
    mongo_client.close()
    print("MongoDB 연결 종료")

    if redis_client:
        await redis_client.close()
        print("Redis 연결 종료")


# ===========================================================================
# FastAPI 앱 인스턴스 생성
# ===========================================================================

app = FastAPI(
    title="NoSQL 학습 API (MongoDB + Redis)",
    description=(
        "MongoDB를 사용한 문서 기반 CRUD와 "
        "Redis를 활용한 캐싱 패턴을 학습하는 API입니다.\n\n"
        "**사전 조건**: MongoDB(localhost:27017)와 Redis(localhost:6379)가 실행 중이어야 합니다."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ===========================================================================
# MongoDB 컬렉션 접근 헬퍼
# ===========================================================================


def _get_collection():
    """MongoDB 컬렉션 객체를 반환합니다."""
    db = mongo_client[MONGODB_DB_NAME]
    return db[MONGODB_COLLECTION_NAME]


# ===========================================================================
# 게시글(Post) CRUD 엔드포인트
# ===========================================================================


@app.post(
    "/posts/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새 게시글 생성",
)
async def create_post(post_data: PostCreate):
    """
    MongoDB에 새로운 게시글 문서를 생성합니다.

    - `insert_one()` : 단일 문서를 컬렉션에 삽입
    - MongoDB가 자동으로 `_id` (ObjectId)를 생성합니다
    - 생성/수정 일시를 UTC 기준으로 기록합니다
    """
    collection = _get_collection()

    # 현재 UTC 시각
    now = datetime.now(timezone.utc)

    # MongoDB에 저장할 문서(dict) 생성
    document = {
        "title": post_data.title,
        "content": post_data.content,
        "author": post_data.author,
        "tags": post_data.tags,
        "created_at": now,
        "updated_at": now,
    }

    # MongoDB에 문서 삽입
    result = await collection.insert_one(document)

    # 삽입된 문서를 다시 조회하여 반환 (_id 포함)
    created_doc = await collection.find_one({"_id": result.inserted_id})
    return _post_document_to_response(created_doc)


@app.get(
    "/posts/",
    response_model=list[PostResponse],
    summary="게시글 목록 조회",
)
async def read_posts(
    skip: int = Query(default=0, ge=0, description="건너뛸 문서 수"),
    limit: int = Query(default=20, ge=1, le=100, description="최대 조회 수"),
    tag: Optional[str] = Query(default=None, description="태그로 필터링"),
    author: Optional[str] = Query(default=None, description="작성자로 필터링"),
):
    """
    게시글 목록을 조회합니다.

    - `find()` : 조건에 맞는 문서를 검색 (필터 미지정 시 전체 조회)
    - `skip()` / `limit()` : 페이지네이션 지원
    - `sort()` : 최신 순으로 정렬
    - 태그 또는 작성자로 필터링이 가능합니다
    """
    collection = _get_collection()

    # 필터 조건 구성 (MongoDB 쿼리 필터)
    query_filter: dict = {}

    if tag:
        # tags 배열에 해당 태그가 포함된 문서를 검색
        query_filter["tags"] = tag

    if author:
        # 작성자 이름으로 필터링
        query_filter["author"] = author

    # MongoDB에서 문서 목록 조회
    # - find() : 조건에 맞는 커서(Cursor) 반환
    # - sort() : 생성일 기준 내림차순 정렬 (-1 = 내림차순)
    # - skip() / limit() : 페이지네이션
    cursor = collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)

    # 커서를 리스트로 변환
    posts = []
    async for doc in cursor:
        posts.append(_post_document_to_response(doc))

    return posts


@app.get(
    "/posts/{post_id}",
    response_model=CacheStatusResponse,
    summary="특정 게시글 조회 (캐싱 적용)",
)
async def read_post(post_id: str):
    """
    특정 게시글을 조회합니다. Redis 캐싱이 적용됩니다.

    **캐싱 흐름:**
    1. Redis에서 캐시된 데이터를 먼저 확인합니다 (캐시 히트)
    2. 캐시가 없으면 MongoDB에서 조회합니다 (캐시 미스)
    3. MongoDB에서 조회한 데이터를 Redis에 캐싱합니다 (TTL 설정)
    4. 응답에 데이터 출처(source)를 포함하여 캐시 동작을 확인할 수 있습니다

    - `find_one()` : 조건에 맞는 단일 문서를 조회
    """
    # ObjectId 형식 유효성 검사
    if not ObjectId.is_valid(post_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{post_id}'는 유효한 ObjectId 형식이 아닙니다.",
        )

    cache_key = _get_cache_key(post_id)

    # ----- 1단계: Redis 캐시 확인 -----
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            # 캐시 히트 - Redis에서 바로 반환
            post_dict = json.loads(cached_data)
            return CacheStatusResponse(
                source="cache",
                post=PostResponse(**post_dict),
            )
    except Exception:
        # Redis 연결 실패 시 캐시 없이 진행
        pass

    # ----- 2단계: MongoDB에서 조회 (캐시 미스) -----
    collection = _get_collection()
    doc = await collection.find_one({"_id": ObjectId(post_id)})

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"게시글 ID '{post_id}'를 찾을 수 없습니다.",
        )

    post_response = _post_document_to_response(doc)

    # ----- 3단계: Redis에 캐싱 (TTL 설정) -----
    try:
        # JSON 문자열로 직렬화하여 Redis에 저장
        # ex=REDIS_CACHE_TTL : TTL(초) 설정 - 시간이 지나면 자동 삭제
        await redis_client.set(
            cache_key,
            post_response.model_dump_json(),
            ex=REDIS_CACHE_TTL,
        )
    except Exception:
        # Redis 저장 실패 시에도 응답은 정상 반환
        pass

    return CacheStatusResponse(
        source="database",
        post=post_response,
    )


@app.put(
    "/posts/{post_id}",
    response_model=PostResponse,
    summary="게시글 수정",
)
async def update_post(post_id: str, post_data: PostUpdate):
    """
    게시글을 부분 수정합니다.

    - `update_one()` : 조건에 맞는 단일 문서를 수정
    - `$set` 연산자 : 지정된 필드만 업데이트 (나머지 필드는 유지)
    - 수정 후 해당 게시글의 캐시를 무효화합니다
    """
    # ObjectId 형식 유효성 검사
    if not ObjectId.is_valid(post_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{post_id}'는 유효한 ObjectId 형식이 아닙니다.",
        )

    collection = _get_collection()

    # None이 아닌 필드만 업데이트 데이터로 구성
    update_data = {
        key: value
        for key, value in post_data.model_dump().items()
        if value is not None
    }

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 필드가 하나 이상 필요합니다.",
        )

    # 수정 일시 추가
    update_data["updated_at"] = datetime.now(timezone.utc)

    # MongoDB 문서 수정
    # - $set : 지정된 필드만 변경 (다른 필드에는 영향 없음)
    result = await collection.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": update_data},
    )

    # matched_count : 필터 조건에 맞는 문서 수
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"게시글 ID '{post_id}'를 찾을 수 없습니다.",
        )

    # 캐시 무효화 - 수정된 데이터와 캐시 데이터의 불일치 방지
    await _invalidate_cache(post_id)

    # 수정된 문서를 다시 조회하여 반환
    updated_doc = await collection.find_one({"_id": ObjectId(post_id)})
    return _post_document_to_response(updated_doc)


@app.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="게시글 삭제",
)
async def delete_post(post_id: str):
    """
    게시글을 삭제합니다.

    - `delete_one()` : 조건에 맞는 단일 문서를 삭제
    - 삭제 후 해당 게시글의 캐시도 함께 무효화합니다
    """
    # ObjectId 형식 유효성 검사
    if not ObjectId.is_valid(post_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{post_id}'는 유효한 ObjectId 형식이 아닙니다.",
        )

    collection = _get_collection()

    # MongoDB 문서 삭제
    result = await collection.delete_one({"_id": ObjectId(post_id)})

    # deleted_count : 실제로 삭제된 문서 수
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"게시글 ID '{post_id}'를 찾을 수 없습니다.",
        )

    # 캐시 무효화
    await _invalidate_cache(post_id)


# ===========================================================================
# Redis 캐싱 유틸리티 엔드포인트
# ===========================================================================


@app.get(
    "/cache/stats",
    summary="Redis 캐시 상태 확인",
)
async def get_cache_stats():
    """
    Redis 서버의 기본 상태 정보를 반환합니다.

    - 연결 상태, 사용 중인 메모리, 저장된 키 수 등을 확인할 수 있습니다.
    """
    try:
        info = await redis_client.info("memory")
        db_size = await redis_client.dbsize()
        return {
            "status": "connected",
            "used_memory_human": info.get("used_memory_human", "알 수 없음"),
            "total_keys": db_size,
            "cache_ttl_seconds": REDIS_CACHE_TTL,
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e),
        }


@app.delete(
    "/cache/clear",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="전체 캐시 초기화",
)
async def clear_cache():
    """
    Redis에 저장된 모든 캐시를 삭제합니다.

    주의: 현재 Redis 데이터베이스의 모든 키가 삭제됩니다.
    프로덕션 환경에서는 패턴 기반 삭제를 사용하는 것이 안전합니다.
    """
    try:
        await redis_client.flushdb()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐시 초기화 실패: {str(e)}",
        )


# ===========================================================================
# 헬스 체크 엔드포인트
# ===========================================================================


@app.get("/health", summary="서버 상태 확인")
async def health_check():
    """MongoDB와 Redis의 연결 상태를 확인합니다."""
    health = {
        "status": "healthy",
        "mongodb": "disconnected",
        "redis": "disconnected",
    }

    # MongoDB 연결 확인
    try:
        await mongo_client.admin.command("ping")
        health["mongodb"] = "connected"
    except Exception:
        health["status"] = "degraded"

    # Redis 연결 확인
    try:
        await redis_client.ping()
        health["redis"] = "connected"
    except Exception:
        health["status"] = "degraded"

    return health
