"""
Chapter 22: FastAPI 성능 최적화
================================
인메모리 캐싱을 활용한 성능 최적화 예제.
캐시 적용 전후의 응답 시간을 비교하고, 캐시 통계를 확인할 수 있다.

실행 방법:
    uvicorn main:app --reload

프로덕션 실행:
    gunicorn -c gunicorn.conf.py main:app
"""

import asyncio
import functools
import hashlib
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

# ============================================================
# FastAPI 애플리케이션 인스턴스 생성
# ============================================================
app = FastAPI(
    title="FastAPI 성능 최적화 학습",
    version="1.0.0",
    description="인메모리 캐싱과 응답 시간 측정을 통한 성능 최적화 학습용 애플리케이션",
)


# ============================================================
# 인메모리 캐시 구현
# ============================================================
# TTL(Time To Live) 기반 캐시 저장소
# 각 항목은 (값, 만료시각) 튜플로 저장된다
class InMemoryCache:
    """
    TTL 기반 인메모리 캐시.
    단일 워커 환경에서 간단하게 사용할 수 있는 캐시 구현체이다.
    다중 워커 환경에서는 Redis 등 외부 캐시 사용을 권장한다.
    """

    def __init__(self) -> None:
        # 캐시 데이터 저장소: {키: (값, 만료시각)}
        self._store: dict[str, tuple[Any, float]] = {}
        # 캐시 통계 정보
        self._hits: int = 0      # 캐시 적중 횟수
        self._misses: int = 0    # 캐시 미스 횟수

    def get(self, key: str) -> Any | None:
        """
        캐시에서 값을 조회한다.
        만료된 항목은 자동으로 삭제하고 None을 반환한다.
        """
        if key in self._store:
            value, expires_at = self._store[key]
            # 만료 시간이 지나지 않았으면 캐시 적중
            if time.time() < expires_at:
                self._hits += 1
                return value
            # 만료된 항목은 삭제한다
            del self._store[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """
        캐시에 값을 저장한다.
        ttl: 캐시 유지 시간 (초 단위, 기본 60초)
        """
        expires_at = time.time() + ttl
        self._store[key] = (value, expires_at)

    def clear(self) -> None:
        """캐시를 전체 초기화한다."""
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def cleanup_expired(self) -> int:
        """
        만료된 캐시 항목을 정리한다.
        정리된 항목의 수를 반환한다.
        """
        now = time.time()
        expired_keys = [
            key for key, (_, expires_at) in self._store.items()
            if now >= expires_at
        ]
        for key in expired_keys:
            del self._store[key]
        return len(expired_keys)

    @property
    def stats(self) -> dict[str, Any]:
        """캐시 통계 정보를 반환한다."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "total_entries": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
        }


# 전역 캐시 인스턴스 생성
cache = InMemoryCache()


# ============================================================
# 캐시 데코레이터
# ============================================================
def cached(ttl: int = 60):
    """
    비동기 함수용 캐시 데코레이터.
    함수의 인자를 기반으로 캐시 키를 생성하고,
    TTL 기간 동안 동일한 인자에 대해 캐시된 결과를 반환한다.

    사용 예:
        @cached(ttl=30)
        async def my_function(param: str) -> dict:
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 함수명과 인자를 조합하여 고유한 캐시 키를 생성한다
            key_source = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_source.encode()).hexdigest()

            # 캐시에서 조회한다
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 캐시 미스: 실제 함수를 실행한다
            result = await func(*args, **kwargs)

            # 결과를 캐시에 저장한다
            cache.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


# ============================================================
# 응답 모델 정의
# ============================================================
class ComputationResult(BaseModel):
    """연산 결과 응답 모델"""
    result: float
    input_value: int
    elapsed_ms: float
    cached: bool
    timestamp: str


class CacheStatsResponse(BaseModel):
    """캐시 통계 응답 모델"""
    total_entries: int
    hits: int
    misses: int
    total_requests: int
    hit_rate_percent: float


class ComparisonResponse(BaseModel):
    """성능 비교 응답 모델"""
    slow_elapsed_ms: float
    cached_elapsed_ms: float
    speedup_factor: float
    message: str


# ============================================================
# 미들웨어: 응답 시간 측정
# ============================================================
@app.middleware("http")
async def add_process_time_header(request: Request, call_next) -> Response:
    """
    모든 요청의 처리 시간을 측정하여 응답 헤더에 추가하는 미들웨어.
    X-Process-Time 헤더를 통해 서버 측 처리 시간을 확인할 수 있다.
    프로파일링과 성능 모니터링에 유용하다.
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    # 밀리초 단위로 변환하여 헤더에 추가한다
    response.headers["X-Process-Time"] = f"{process_time * 1000:.2f}ms"
    return response


# ============================================================
# 무거운 연산 시뮬레이션 함수
# ============================================================
async def heavy_computation(n: int) -> float:
    """
    무거운 연산을 시뮬레이션하는 함수.
    실제 프로덕션에서는 외부 API 호출, 데이터베이스 쿼리,
    복잡한 비즈니스 로직 등이 이에 해당한다.
    비동기 sleep으로 I/O 바운드 작업을 모사한다.
    """
    # 비동기 대기로 네트워크 지연을 시뮬레이션한다 (0.5초)
    await asyncio.sleep(0.5)
    # CPU 바운드 연산을 시뮬레이션한다
    result = sum(i * i for i in range(n * 1000))
    return float(result)


@cached(ttl=30)
async def cached_heavy_computation(n: int) -> float:
    """
    캐시가 적용된 무거운 연산 함수.
    동일한 입력에 대해 30초간 캐시된 결과를 반환한다.
    """
    return await heavy_computation(n)


# ============================================================
# API 엔드포인트
# ============================================================
@app.get("/", summary="환영 메시지")
async def root() -> dict[str, str]:
    """루트 엔드포인트: 성능 최적화 학습 앱 환영 메시지를 반환한다."""
    return {
        "message": "FastAPI 성능 최적화 학습에 오신 것을 환영합니다!",
        "docs": "/docs",
    }


@app.get(
    "/slow",
    response_model=ComputationResult,
    summary="캐시 미적용 엔드포인트 (느림)",
    description="매 요청마다 무거운 연산을 수행한다. 캐시가 적용되지 않아 항상 동일한 시간이 소요된다.",
)
async def slow_endpoint(n: int = 100) -> ComputationResult:
    """
    캐시가 적용되지 않은 엔드포인트.
    매번 무거운 연산을 수행하므로 응답 시간이 일정하게 느리다.
    /cached 엔드포인트와 비교하여 캐싱의 효과를 확인할 수 있다.
    """
    start = time.perf_counter()
    result = await heavy_computation(n)
    elapsed = (time.perf_counter() - start) * 1000  # 밀리초 변환

    return ComputationResult(
        result=result,
        input_value=n,
        elapsed_ms=round(elapsed, 2),
        cached=False,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get(
    "/cached",
    response_model=ComputationResult,
    summary="캐시 적용 엔드포인트 (빠름)",
    description="동일한 입력에 대해 캐시된 결과를 반환한다. TTL(30초) 내에는 즉시 응답한다.",
)
async def cached_endpoint(n: int = 100) -> ComputationResult:
    """
    캐시가 적용된 엔드포인트.
    첫 번째 요청은 실제 연산을 수행하지만,
    이후 동일한 입력에 대해서는 캐시된 결과를 즉시 반환한다.
    """
    start = time.perf_counter()
    result = await cached_heavy_computation(n)
    elapsed = (time.perf_counter() - start) * 1000  # 밀리초 변환

    # 캐시 적중 여부를 판단한다 (1ms 미만이면 캐시에서 반환된 것으로 간주)
    is_cached = elapsed < 1.0

    return ComputationResult(
        result=result,
        input_value=n,
        elapsed_ms=round(elapsed, 2),
        cached=is_cached,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get(
    "/compare",
    response_model=ComparisonResponse,
    summary="성능 비교",
    description="캐시 미적용과 적용 엔드포인트의 응답 시간을 한 번에 비교한다.",
)
async def compare_performance(n: int = 100) -> ComparisonResponse:
    """
    캐시 적용 전후의 성능을 비교하는 엔드포인트.
    캐시 워밍업 후 캐시된 버전과 미캐시 버전의 처리 시간을 측정한다.
    """
    # 캐시 미적용: 무거운 연산을 직접 실행한다
    start_slow = time.perf_counter()
    await heavy_computation(n)
    slow_elapsed = (time.perf_counter() - start_slow) * 1000

    # 캐시 워밍업: 첫 번째 호출로 캐시를 채운다
    await cached_heavy_computation(n)

    # 캐시 적용: 캐시된 결과를 반환한다
    start_cached = time.perf_counter()
    await cached_heavy_computation(n)
    cached_elapsed = (time.perf_counter() - start_cached) * 1000

    # 성능 향상 비율을 계산한다
    speedup = slow_elapsed / cached_elapsed if cached_elapsed > 0 else float("inf")

    return ComparisonResponse(
        slow_elapsed_ms=round(slow_elapsed, 2),
        cached_elapsed_ms=round(cached_elapsed, 2),
        speedup_factor=round(speedup, 1),
        message=f"캐시 적용 시 약 {speedup:.1f}배 빠릅니다.",
    )


@app.get(
    "/stats",
    response_model=CacheStatsResponse,
    summary="캐시 통계",
    description="캐시 적중률, 저장된 항목 수 등 캐시 운영 통계를 반환한다.",
)
async def cache_stats() -> CacheStatsResponse:
    """
    캐시 통계 엔드포인트.
    캐시 적중률(hit rate)을 통해 캐시 전략의 효과를 모니터링할 수 있다.
    적중률이 낮다면 TTL 조정이나 캐시 키 전략 변경을 고려한다.
    """
    stats = cache.stats
    return CacheStatsResponse(**stats)


@app.post(
    "/cache/clear",
    summary="캐시 초기화",
    description="모든 캐시 항목과 통계를 초기화한다.",
)
async def clear_cache() -> dict[str, str]:
    """캐시를 전체 초기화하는 엔드포인트. 테스트나 디버깅 시 사용한다."""
    cache.clear()
    return {"message": "캐시가 초기화되었습니다."}


@app.post(
    "/cache/cleanup",
    summary="만료된 캐시 정리",
    description="만료된 캐시 항목을 수동으로 정리한다.",
)
async def cleanup_cache() -> dict[str, Any]:
    """만료된 캐시 항목을 정리하는 엔드포인트."""
    removed_count = cache.cleanup_expired()
    return {
        "message": f"만료된 캐시 항목 {removed_count}개를 정리했습니다.",
        "removed_count": removed_count,
    }


@app.get(
    "/health",
    summary="헬스체크",
    description="서비스 상태를 확인하는 엔드포인트.",
)
async def health_check() -> dict[str, str]:
    """헬스체크 엔드포인트. 정상 동작 시 healthy 상태를 반환한다."""
    return {"status": "healthy"}
