# Chapter 19: 백그라운드 태스크 (Background Tasks)

## 학습 목표

- FastAPI의 `BackgroundTasks`를 사용하여 백그라운드 작업을 수행할 수 있다
- 응답 반환 후 비동기로 실행되는 작업의 개념을 이해한다
- 백그라운드 태스크의 적절한 사용 사례를 파악한다
- 하나의 엔드포인트에서 여러 백그라운드 태스크를 등록하는 방법을 익힌다
- Celery 같은 분산 태스크 큐와의 차이점을 이해한다

## 핵심 개념

### 1. BackgroundTasks란?

`BackgroundTasks`는 FastAPI가 제공하는 기능으로, HTTP 응답을 클라이언트에게 먼저 반환한 후 백그라운드에서 추가 작업을 수행한다. 이를 통해 사용자는 느린 작업(이메일 발송, 로그 기록 등)이 완료될 때까지 기다릴 필요가 없다.

```python
from fastapi import BackgroundTasks

@app.post("/items/")
async def create_item(background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, "아이템이 생성되었습니다")
    return {"message": "아이템 생성 완료"}
```

### 2. 사용 사례

| 사용 사례 | 설명 |
|-----------|------|
| 이메일 발송 | 회원가입/주문 확인 메일을 응답 후 발송 |
| 로그 기록 | 파일이나 외부 시스템에 로그를 기록 |
| 알림 전송 | 푸시 알림, SMS 등을 비동기로 전송 |
| 데이터 처리 | 가벼운 데이터 후처리 작업 수행 |
| 캐시 갱신 | 응답 후 캐시를 업데이트 |

### 3. BackgroundTasks vs Celery

| 항목 | BackgroundTasks | Celery |
|------|----------------|--------|
| 실행 환경 | 같은 프로세스 내에서 실행 | 별도 워커 프로세스에서 실행 |
| 브로커 필요 | 불필요 | Redis/RabbitMQ 필요 |
| 설정 복잡도 | 매우 간단 | 상대적으로 복잡 |
| 적합한 작업 | 가벼운 작업 (로그, 알림) | 무거운 작업 (영상 처리, ML 학습) |
| 재시도 | 기본 미지원 | 내장 재시도 메커니즘 |
| 모니터링 | 기본 미지원 | Flower 등 모니터링 도구 |
| 스케줄링 | 미지원 | Celery Beat로 가능 |

**요약**: 간단하고 가벼운 작업에는 `BackgroundTasks`를, 복잡하고 무거운 작업에는 Celery를 사용한다.

### 4. 주의사항

- 백그라운드 태스크는 같은 프로세스에서 실행되므로, 서버가 종료되면 미완료 태스크도 중단된다
- CPU 집약적인 무거운 작업은 Celery 같은 별도 워커를 사용해야 한다
- 백그라운드 태스크에서 발생한 예외는 클라이언트에게 전달되지 않으므로, 적절한 에러 처리가 필요하다

## 코드 실행 방법

### 사전 준비

```bash
pip install fastapi uvicorn
```

### 앱 실행

```bash
uvicorn main:app --reload
```

### API 테스트

```bash
# 아이템 생성 (백그라운드로 로그 기록)
curl -X POST "http://localhost:8000/items/" \
  -H "Content-Type: application/json" \
  -d '{"name": "노트북", "price": 1500000}'

# 알림 발송 (백그라운드로 알림 전송 시뮬레이션)
curl -X POST "http://localhost:8000/send-notification/user@example.com"

# 로그 파일 확인
cat log.txt
```

### Swagger UI에서 테스트

브라우저에서 `http://localhost:8000/docs` 접속

## 실습 포인트

1. **기본 백그라운드 태스크**: `write_log()` 함수가 응답 후 파일에 로그를 기록하는 것을 확인한다
2. **느린 작업 시뮬레이션**: `send_notification()`이 `time.sleep`으로 지연되지만 응답은 즉시 반환되는 것을 확인한다
3. **다중 태스크 등록**: 하나의 엔드포인트에서 여러 백그라운드 태스크를 등록하고 모두 실행되는지 확인한다
4. **로그 파일 확인**: `log.txt` 파일이 생성되고 내용이 추가되는 것을 확인한다
5. **응답 시간 비교**: 백그라운드 태스크 유무에 따른 응답 속도 차이를 체감한다

## 참고 자료

- [FastAPI 공식 문서 - Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Starlette BackgroundTasks](https://www.starlette.io/background/)
- [Celery 공식 문서](https://docs.celeryq.dev/)
