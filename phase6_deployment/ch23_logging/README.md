# Chapter 23: 로깅과 모니터링

## 학습 목표

- Python `logging` 모듈의 구조와 핵심 개념을 이해한다
- 구조화 로깅(Structured Logging)을 JSON 포맷으로 구현할 수 있다
- FastAPI 미들웨어를 활용한 요청/응답 로깅 패턴을 익힌다
- Health Check 엔드포인트 설계 패턴을 학습한다
- 운영 환경 모니터링의 기초 개념을 파악한다

## 핵심 개념

### 1. Python logging 모듈 기본

Python 표준 라이브러리 `logging` 모듈은 계층적 로거 시스템을 제공한다.

| 구성 요소 | 역할 |
|-----------|------|
| **Logger** | 로그 메시지를 생성하는 진입점 |
| **Handler** | 로그 메시지를 출력 대상(콘솔, 파일 등)으로 전달 |
| **Formatter** | 로그 메시지의 출력 형식을 결정 |
| **Filter** | 특정 조건에 따라 로그를 필터링 |

### 2. 로그 레벨

| 레벨 | 숫자 값 | 용도 |
|------|---------|------|
| `DEBUG` | 10 | 디버깅용 상세 정보 |
| `INFO` | 20 | 정상 동작 확인 메시지 |
| `WARNING` | 30 | 잠재적 문제 경고 |
| `ERROR` | 40 | 오류 발생, 기능 수행 실패 |
| `CRITICAL` | 50 | 심각한 오류, 프로그램 종료 가능 |

### 3. 구조화 로깅 (Structured Logging)

일반 텍스트 로그 대신 JSON 포맷으로 로그를 출력하면 다음과 같은 이점이 있다:

- **파싱 용이**: ELK Stack, Datadog 등 로그 수집 도구와 쉽게 연동
- **검색 효율**: 필드 기반 검색 및 필터링 가능
- **일관성**: 모든 로그가 동일한 구조를 가짐

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "level": "INFO",
  "message": "요청 처리 완료",
  "method": "GET",
  "path": "/api/users",
  "status_code": 200,
  "duration_ms": 45.2
}
```

### 4. Health Check 엔드포인트 패턴

운영 환경에서 서비스 상태를 확인하기 위한 표준 패턴이다.

- **GET /health**: 기본 서비스 생존 확인 (liveness)
- **GET /health/db**: 데이터베이스 연결 상태 확인 (readiness)
- Kubernetes, 로드밸런서 등에서 주기적으로 호출하여 서비스 상태를 판단

### 5. 요청 로깅 미들웨어

모든 HTTP 요청과 응답을 자동으로 로깅하는 미들웨어를 통해:

- 요청 메서드, 경로, 상태 코드, 처리 시간을 기록
- 별도의 코드 수정 없이 전체 API에 일괄 적용
- 성능 병목 지점 파악 및 트래픽 분석에 활용

## 코드 실행 방법

### 의존성 설치

```bash
pip install fastapi uvicorn python-json-logger
```

### 서버 실행

```bash
cd phase6_deployment/ch23_logging
uvicorn main:app --reload
```

### 주요 엔드포인트 테스트

```bash
# 기본 Health Check
curl http://localhost:8000/health

# DB Health Check
curl http://localhost:8000/health/db

# 다양한 로그 레벨 테스트
curl http://localhost:8000/log/info
curl http://localhost:8000/log/warning
curl http://localhost:8000/log/error

# Swagger UI 확인
open http://localhost:8000/docs
```

## 실습 포인트

1. **로그 레벨 변경 실습**: `logging.DEBUG`로 레벨을 변경하고 출력 차이를 관찰한다
2. **JSON 로그 확인**: 터미널에 출력되는 JSON 로그의 구조를 확인하고 `jq`로 파싱해본다
   ```bash
   uvicorn main:app 2>&1 | jq '.'
   ```
3. **미들웨어 동작 확인**: 여러 엔드포인트를 호출하며 자동으로 기록되는 요청 로그를 관찰한다
4. **Health Check 활용**: `/health` 응답을 기반으로 서비스 모니터링 시나리오를 구상해본다
5. **커스텀 필드 추가**: 로그에 `request_id`, `user_agent` 등 추가 필드를 넣어본다
6. **파일 핸들러 추가**: `FileHandler`를 추가하여 로그를 파일로도 저장해본다
