"""
Chapter 07: 비동기 프로그래밍 (Async/Await)

async/await 패턴, 동시성 vs 병렬성, FastAPI의 def vs async def 차이,
httpx를 이용한 비동기 HTTP 호출, asyncio.gather를 활용한 동시 실행을 학습한다.

실행 방법:
    pip install httpx
    uvicorn main:app --reload
"""

import asyncio
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI


# ============================================================
# httpx.AsyncClient 수명 주기 관리
# - 앱 시작 시 클라이언트를 생성하고, 종료 시 닫는다
# - 매 요청마다 클라이언트를 생성하는 것보다 효율적 (커넥션 풀 재사용)
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱 수명 주기 관리.
    시작 시 httpx.AsyncClient를 생성하고, 종료 시 안전하게 닫는다.
    """
    # 시작 시 실행: 비동기 HTTP 클라이언트 생성
    app.state.http_client = httpx.AsyncClient(
        base_url="https://jsonplaceholder.typicode.com",
        timeout=10.0,  # 10초 타임아웃 설정
    )
    print("[앱 시작] httpx.AsyncClient 생성 완료")
    yield
    # 종료 시 실행: HTTP 클라이언트 정리
    await app.state.http_client.aclose()
    print("[앱 종료] httpx.AsyncClient 종료 완료")


app = FastAPI(
    title="Chapter 07: 비동기 프로그래밍",
    description="async/await, 동시성, 비동기 HTTP 호출 학습",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# JSONPlaceholder API 기본 URL
# - 무료 테스트용 REST API
# - Posts, Users, Comments 등의 가짜 데이터 제공
# ============================================================
JSONPLACEHOLDER_BASE = "https://jsonplaceholder.typicode.com"


# ============================================================
# 1. def (동기) vs async def (비동기) 엔드포인트 비교
# - def: FastAPI가 별도 스레드풀(threadpool)에서 실행
# - async def: 이벤트 루프에서 직접 실행
# ============================================================
@app.get("/sync", tags=["동기 vs 비동기"])
def sync_endpoint():
    """
    동기(sync) 엔드포인트.
    FastAPI가 내부적으로 스레드풀에서 실행하므로 이벤트 루프를 블로킹하지 않는다.
    블로킹 I/O 작업이 있을 때 일반 def를 사용하는 것이 안전하다.
    """
    start = time.time()
    # time.sleep은 블로킹 호출이지만,
    # def 함수이므로 스레드풀에서 실행되어 다른 요청에 영향을 주지 않음
    time.sleep(1)
    elapsed = round(time.time() - start, 3)
    return {
        "type": "동기 (sync)",
        "설명": "def 함수는 스레드풀에서 실행됨",
        "소요시간_초": elapsed,
    }


@app.get("/async", tags=["동기 vs 비동기"])
async def async_endpoint():
    """
    비동기(async) 엔드포인트.
    이벤트 루프에서 직접 실행되며, await 지점에서 다른 작업에 제어권을 양보한다.
    """
    start = time.time()
    # asyncio.sleep은 논블로킹 호출
    # await 시 이벤트 루프에 제어권을 양보하여 다른 요청 처리 가능
    await asyncio.sleep(1)
    elapsed = round(time.time() - start, 3)
    return {
        "type": "비동기 (async)",
        "설명": "async def 함수는 이벤트 루프에서 실행됨",
        "소요시간_초": elapsed,
    }


# ============================================================
# 2. asyncio.sleep vs time.sleep 차이 시연
# - asyncio.sleep: 논블로킹 (이벤트 루프 제어권 양보)
# - time.sleep: 블로킹 (스레드 전체를 멈춤)
# ============================================================
@app.get("/sleep/async/{seconds}", tags=["sleep 비교"])
async def async_sleep_demo(seconds: float):
    """
    asyncio.sleep 시연.
    대기 중 다른 요청을 처리할 수 있어 서버 효율이 높다.
    """
    start = time.time()
    await asyncio.sleep(seconds)
    elapsed = round(time.time() - start, 3)
    return {
        "방식": "asyncio.sleep (논블로킹)",
        "요청_대기시간_초": seconds,
        "실제_소요시간_초": elapsed,
        "특징": "대기 중 다른 요청 처리 가능",
    }


@app.get("/sleep/sync/{seconds}", tags=["sleep 비교"])
def sync_sleep_demo(seconds: float):
    """
    time.sleep 시연.
    def 함수이므로 스레드풀에서 실행되어 이벤트 루프는 블로킹되지 않는다.
    다만, 스레드풀 크기에 제한이 있으므로 대량의 요청 시 주의가 필요하다.
    """
    start = time.time()
    time.sleep(seconds)
    elapsed = round(time.time() - start, 3)
    return {
        "방식": "time.sleep (블로킹, 스레드풀에서 실행)",
        "요청_대기시간_초": seconds,
        "실제_소요시간_초": elapsed,
        "특징": "def 함수이므로 스레드풀에서 실행됨",
    }


# ============================================================
# 3. httpx.AsyncClient로 외부 API 비동기 호출
# - JSONPlaceholder API (https://jsonplaceholder.typicode.com)
# - 비동기 HTTP 클라이언트로 외부 서비스 호출
# ============================================================
@app.get("/external/posts/{post_id}", tags=["외부 API 호출"])
async def fetch_post(post_id: int):
    """
    외부 API에서 게시글을 비동기로 조회한다.
    httpx.AsyncClient는 await로 호출하여 이벤트 루프를 블로킹하지 않는다.
    """
    client: httpx.AsyncClient = app.state.http_client
    start = time.time()
    response = await client.get(f"/posts/{post_id}")
    elapsed = round(time.time() - start, 3)

    if response.status_code != 200:
        return {
            "error": f"외부 API 호출 실패 (상태 코드: {response.status_code})",
            "소요시간_초": elapsed,
        }

    return {
        "message": "외부 API에서 게시글 조회 성공",
        "소요시간_초": elapsed,
        "data": response.json(),
    }


@app.get("/external/users/{user_id}", tags=["외부 API 호출"])
async def fetch_user(user_id: int):
    """
    외부 API에서 사용자 정보를 비동기로 조회한다.
    """
    client: httpx.AsyncClient = app.state.http_client
    start = time.time()
    response = await client.get(f"/users/{user_id}")
    elapsed = round(time.time() - start, 3)

    if response.status_code != 200:
        return {
            "error": f"외부 API 호출 실패 (상태 코드: {response.status_code})",
            "소요시간_초": elapsed,
        }

    return {
        "message": "외부 API에서 사용자 정보 조회 성공",
        "소요시간_초": elapsed,
        "data": response.json(),
    }


# ============================================================
# 4. asyncio.gather로 여러 비동기 작업 동시 실행
# - 여러 API 호출을 동시에 실행하여 전체 소요 시간을 단축
# - 순차 실행 대비 큰 성능 향상을 기대할 수 있음
# ============================================================
@app.get("/external/posts-with-users", tags=["asyncio.gather"])
async def fetch_posts_with_users():
    """
    게시글 목록과 사용자 목록을 동시에 조회한다.
    asyncio.gather를 사용하여 두 API 호출을 병렬로 실행한다.

    순차 실행: 각 요청이 200ms라면 총 400ms
    동시 실행: asyncio.gather로 총 약 200ms (가장 오래 걸리는 요청 기준)
    """
    client: httpx.AsyncClient = app.state.http_client
    start = time.time()

    # asyncio.gather: 여러 코루틴을 동시에 실행하고 모든 결과를 기다림
    posts_response, users_response = await asyncio.gather(
        client.get("/posts", params={"_limit": 5}),  # 게시글 5개 조회
        client.get("/users", params={"_limit": 5}),   # 사용자 5명 조회
    )
    elapsed = round(time.time() - start, 3)

    return {
        "message": "asyncio.gather로 게시글과 사용자를 동시에 조회",
        "소요시간_초": elapsed,
        "posts": posts_response.json(),
        "users": users_response.json(),
    }


@app.get("/external/user-with-posts/{user_id}", tags=["asyncio.gather"])
async def fetch_user_with_posts(user_id: int):
    """
    특정 사용자 정보와 해당 사용자의 게시글을 동시에 조회한다.
    두 개의 독립적인 API 호출을 동시에 실행한다.
    """
    client: httpx.AsyncClient = app.state.http_client
    start = time.time()

    # 사용자 정보와 해당 사용자의 게시글을 동시에 조회
    user_response, posts_response = await asyncio.gather(
        client.get(f"/users/{user_id}"),
        client.get("/posts", params={"userId": user_id}),
    )
    elapsed = round(time.time() - start, 3)

    return {
        "message": f"사용자 {user_id}의 정보와 게시글을 동시에 조회",
        "소요시간_초": elapsed,
        "user": user_response.json(),
        "posts": posts_response.json(),
    }


# ============================================================
# 5. 동시성 성능 비교 엔드포인트
# - 순차 실행 vs 동시 실행의 소요 시간 차이를 직접 확인
# - asyncio.gather의 성능 이점을 수치로 보여줌
# ============================================================
async def _simulate_io_task(task_name: str, duration: float) -> dict:
    """
    I/O 작업을 시뮬레이션하는 비동기 헬퍼 함수.
    asyncio.sleep으로 네트워크/디스크 I/O 대기를 흉내낸다.
    """
    start = time.time()
    await asyncio.sleep(duration)
    elapsed = round(time.time() - start, 3)
    return {
        "task": task_name,
        "duration": duration,
        "actual_elapsed": elapsed,
    }


@app.get("/benchmark/sequential", tags=["성능 비교"])
async def benchmark_sequential():
    """
    순차 실행 벤치마크.
    3개의 비동기 작업을 하나씩 순서대로 실행한다.
    총 소요 시간 = 각 작업의 대기 시간 합산 (약 3초)
    """
    start = time.time()

    # 순차 실행: 각 await가 완료될 때까지 대기 후 다음 작업 시작
    result1 = await _simulate_io_task("DB 조회", 1.0)
    result2 = await _simulate_io_task("외부 API 호출", 1.0)
    result3 = await _simulate_io_task("캐시 조회", 1.0)

    total_elapsed = round(time.time() - start, 3)

    return {
        "방식": "순차 실행 (Sequential)",
        "총_소요시간_초": total_elapsed,
        "설명": "각 작업을 순서대로 실행하여 총 시간이 합산됨",
        "results": [result1, result2, result3],
    }


@app.get("/benchmark/concurrent", tags=["성능 비교"])
async def benchmark_concurrent():
    """
    동시 실행 벤치마크.
    3개의 비동기 작업을 asyncio.gather로 동시에 실행한다.
    총 소요 시간 = 가장 오래 걸리는 작업의 대기 시간 (약 1초)
    """
    start = time.time()

    # 동시 실행: asyncio.gather가 모든 작업을 동시에 시작
    results = await asyncio.gather(
        _simulate_io_task("DB 조회", 1.0),
        _simulate_io_task("외부 API 호출", 1.0),
        _simulate_io_task("캐시 조회", 1.0),
    )

    total_elapsed = round(time.time() - start, 3)

    return {
        "방식": "동시 실행 (Concurrent)",
        "총_소요시간_초": total_elapsed,
        "설명": "모든 작업을 동시에 실행하여 가장 오래 걸리는 작업만큼만 소요됨",
        "results": list(results),
    }


@app.get("/benchmark/compare", tags=["성능 비교"])
async def benchmark_compare():
    """
    순차 실행과 동시 실행의 성능을 한 번에 비교한다.
    동시 실행이 얼마나 효율적인지 수치로 확인할 수 있다.
    """
    tasks_config = [
        ("API 호출 A", 0.5),
        ("API 호출 B", 0.7),
        ("API 호출 C", 0.3),
        ("DB 조회", 0.6),
    ]

    # --- 순차 실행 ---
    seq_start = time.time()
    seq_results = []
    for name, duration in tasks_config:
        result = await _simulate_io_task(name, duration)
        seq_results.append(result)
    seq_elapsed = round(time.time() - seq_start, 3)

    # --- 동시 실행 ---
    con_start = time.time()
    con_results = await asyncio.gather(
        *[_simulate_io_task(name, duration) for name, duration in tasks_config]
    )
    con_elapsed = round(time.time() - con_start, 3)

    # 성능 개선율 계산
    improvement = round((1 - con_elapsed / seq_elapsed) * 100, 1) if seq_elapsed > 0 else 0

    return {
        "순차_실행": {
            "총_소요시간_초": seq_elapsed,
            "results": seq_results,
        },
        "동시_실행": {
            "총_소요시간_초": con_elapsed,
            "results": list(con_results),
        },
        "성능_개선율": f"{improvement}% 빠름",
        "설명": "동시 실행은 I/O 대기 시간이 겹치므로 훨씬 빠르다",
    }


# ============================================================
# 루트 엔드포인트
# ============================================================
@app.get("/", tags=["기본"])
async def root():
    """
    API 루트 엔드포인트.
    이 챕터에서 다루는 비동기 프로그래밍 주제 목록을 반환한다.
    """
    return {
        "chapter": "07 - 비동기 프로그래밍 (Async/Await)",
        "topics": [
            "1. 동기 엔드포인트: GET /sync",
            "2. 비동기 엔드포인트: GET /async",
            "3. asyncio.sleep 시연: GET /sleep/async/{seconds}",
            "4. time.sleep 시연: GET /sleep/sync/{seconds}",
            "5. 외부 API 게시글 조회: GET /external/posts/{post_id}",
            "6. 외부 API 사용자 조회: GET /external/users/{user_id}",
            "7. 동시 조회 (gather): GET /external/posts-with-users",
            "8. 사용자+게시글 동시 조회: GET /external/user-with-posts/{user_id}",
            "9. 순차 실행 벤치마크: GET /benchmark/sequential",
            "10. 동시 실행 벤치마크: GET /benchmark/concurrent",
            "11. 성능 비교: GET /benchmark/compare",
        ],
        "docs": "http://127.0.0.1:8000/docs",
    }
