# Chapter 07: 비동기 프로그래밍 (Async/Await)

## 학습 목표

- Python의 `async`/`await` 문법과 비동기 프로그래밍 개념을 이해한다
- 동시성(Concurrency)과 병렬성(Parallelism)의 차이를 파악한다
- FastAPI에서 `def`와 `async def`의 동작 차이를 이해한다
- 이벤트 루프(Event Loop)의 동작 원리를 학습한다
- `httpx.AsyncClient`를 사용하여 외부 API를 비동기로 호출한다
- `asyncio.gather`를 활용하여 여러 비동기 작업을 동시에 실행한다

## 핵심 개념

### 1. 동시성(Concurrency) vs 병렬성(Parallelism)

| 구분 | 동시성 (Concurrency) | 병렬성 (Parallelism) |
|------|---------------------|---------------------|
| 정의 | 여러 작업을 번갈아가며 처리 | 여러 작업을 동시에 처리 |
| 비유 | 한 사람이 여러 일을 번갈아 처리 | 여러 사람이 각각 일을 처리 |
| 구현 | async/await, 이벤트 루프 | 멀티프로세싱, 멀티스레딩 |
| 적합한 작업 | I/O 바운드 (네트워크, 파일) | CPU 바운드 (계산, 변환) |

### 2. FastAPI의 def vs async def

```python
# 동기 함수: 별도의 스레드풀에서 실행됨
# I/O 작업 시 해당 스레드가 블로킹되지만, 다른 요청은 다른 스레드에서 처리
@app.get("/sync")
def sync_endpoint():
    time.sleep(1)  # 스레드를 블로킹
    return {"type": "sync"}

# 비동기 함수: 이벤트 루프에서 직접 실행됨
# await 지점에서 다른 작업에 제어권을 양보하여 동시성 확보
@app.get("/async")
async def async_endpoint():
    await asyncio.sleep(1)  # 이벤트 루프에 제어권 양보
    return {"type": "async"}
```

**주의사항:**
- `async def` 안에서 `time.sleep()`과 같은 블로킹 호출을 사용하면 이벤트 루프 전체가 멈춘다
- 블로킹 I/O가 필요하면 일반 `def` 함수를 사용하거나, `asyncio.to_thread()`를 활용한다

### 3. 이벤트 루프 (Event Loop)

이벤트 루프는 비동기 작업의 스케줄러 역할을 한다.

```
[작업 A: await] -> [작업 B 실행] -> [작업 A 재개] -> [작업 C 실행] -> ...
```

- `await` 키워드를 만나면 현재 작업을 일시 중단하고 다른 작업을 실행
- 대기 중이던 작업이 완료되면 중단된 지점부터 재개
- 이를 통해 단일 스레드에서도 효율적으로 여러 I/O 작업을 처리

### 4. asyncio.gather

여러 비동기 작업을 동시에 실행하고 모든 결과를 한꺼번에 받을 수 있다.

```python
# 순차 실행: 3초 소요 (1 + 1 + 1)
result1 = await fetch_data(1)
result2 = await fetch_data(2)
result3 = await fetch_data(3)

# 동시 실행: 약 1초 소요 (가장 오래 걸리는 작업 기준)
result1, result2, result3 = await asyncio.gather(
    fetch_data(1), fetch_data(2), fetch_data(3)
)
```

## 코드 실행 방법

```bash
# 필요한 패키지 설치
pip install httpx

# 챕터 디렉토리로 이동
cd phase2_core/ch07_async

# 서버 실행
uvicorn main:app --reload

# API 문서 확인
# http://127.0.0.1:8000/docs
```

### 주요 엔드포인트 테스트

```bash
# 동기 vs 비동기 엔드포인트 비교
curl "http://127.0.0.1:8000/sync"
curl "http://127.0.0.1:8000/async"

# 외부 API 비동기 호출
curl "http://127.0.0.1:8000/external/posts/1"
curl "http://127.0.0.1:8000/external/users/1"

# 여러 API 동시 호출 (asyncio.gather)
curl "http://127.0.0.1:8000/external/posts-with-users"

# 동시성 성능 비교 (순차 vs 동시 실행)
curl "http://127.0.0.1:8000/benchmark/sequential"
curl "http://127.0.0.1:8000/benchmark/concurrent"
```

## 실습 포인트

1. **블로킹 실험**: `async def` 안에서 `time.sleep()`을 사용하면 어떤 문제가 발생하는지 확인해 보자
2. **동시성 성능 측정**: 순차 실행과 `asyncio.gather` 동시 실행의 소요 시간을 비교해 보자
3. **외부 API 호출**: JSONPlaceholder API를 활용하여 다양한 리소스를 비동기로 조회해 보자
4. **에러 처리**: 비동기 작업 중 예외가 발생했을 때 `asyncio.gather`의 동작을 실험해 보자
5. **타임아웃 설정**: `httpx.AsyncClient`에 타임아웃을 설정하여 느린 응답을 처리해 보자

## 참고 자료

- [FastAPI 공식 문서 - Async](https://fastapi.tiangolo.com/async/)
- [Python 공식 문서 - asyncio](https://docs.python.org/3/library/asyncio.html)
- [HTTPX 공식 문서](https://www.python-httpx.org/)
