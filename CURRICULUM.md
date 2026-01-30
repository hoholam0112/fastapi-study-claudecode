# FastAPI 학습 커리큘럼 (Python 개발자 -> 중급자)

> 대상: Python을 알고 있는 딥러닝 개발자
> 목표: FastAPI 중급자 수준 도달

---

## Phase 1: 기초 - FastAPI 입문

### 1.1 FastAPI 개요 및 환경 세팅
- FastAPI란 무엇인가 (Starlette + Pydantic 기반)
- Flask/Django와의 차이점
- 프로젝트 환경 구성
  - `python -m venv` 또는 `conda` 가상환경
  - `pip install fastapi uvicorn`
- 첫 번째 앱 실행
  ```python
  from fastapi import FastAPI
  app = FastAPI()

  @app.get("/")
  def root():
      return {"message": "Hello World"}
  ```
- `uvicorn main:app --reload`로 서버 실행
- 자동 생성 문서 확인: `/docs` (Swagger UI), `/redoc`

### 1.2 Path & Query Parameters
- Path Parameter: `/users/{user_id}`
- Query Parameter: `/items?skip=0&limit=10`
- 타입 힌트를 통한 자동 검증
- Optional 파라미터 처리
- Enum을 활용한 파라미터 제한

### 1.3 Request Body와 Pydantic
- Pydantic `BaseModel`로 요청 바디 정의
- 필드 검증 (Field, validator)
- 중첩 모델(Nested Model)
- `Optional`, `default` 값 설정
- 요청 예시:
  ```python
  class Item(BaseModel):
      name: str
      price: float
      is_offer: bool = False
  ```

### 1.4 Response 다루기
- `response_model` 지정
- 상태 코드 설정 (`status_code`)
- Response Model에서 필드 제외 (`response_model_exclude`)
- `JSONResponse`, `HTMLResponse` 등 다양한 응답 타입

### 1.5 CRUD API 실습
- 메모리 기반(dict) 간단한 CRUD API 구현
  - POST: 생성
  - GET: 조회 (단건 / 목록)
  - PUT: 수정
  - DELETE: 삭제

---

## Phase 2: 핵심 기능 익히기

### 2.1 의존성 주입 (Dependency Injection)
- `Depends()` 기본 사용법
- 공통 파라미터 추출 (공통 쿼리 파라미터 등)
- 클래스 기반 의존성
- 의존성 체이닝 (의존성이 다른 의존성을 참조)
- `yield`를 사용한 의존성 (리소스 정리)

### 2.2 비동기 처리 (async/await)
- `def` vs `async def` 차이와 선택 기준
- FastAPI의 비동기 아키텍처 이해
- `httpx.AsyncClient`로 외부 API 비동기 호출
- 동시성(Concurrency) vs 병렬성(Parallelism)
- 딥러닝 추론 서빙 시 `async`를 언제 쓸지 판단하기

### 2.3 에러 핸들링
- `HTTPException` 사용법
- 커스텀 예외 핸들러 등록 (`@app.exception_handler`)
- `RequestValidationError` 핸들링
- 일관된 에러 응답 포맷 설계

### 2.4 미들웨어 (Middleware)
- 미들웨어 개념과 동작 원리
- CORS 미들웨어 설정 (`CORSMiddleware`)
- 커스텀 미들웨어 작성 (요청/응답 로깅 등)
- 요청 처리 시간 측정 미들웨어

### 2.5 Form Data & File Upload
- `Form()` 으로 폼 데이터 받기
- `UploadFile`로 파일 업로드 처리
- 다중 파일 업로드
- 파일 크기 제한 및 타입 검증
- (실습) 이미지 업로드 -> 딥러닝 모델 추론 파이프라인 구성

---

## Phase 3: 데이터베이스 연동

### 3.1 SQLAlchemy + FastAPI
- SQLAlchemy ORM 기본 개념
- 데이터베이스 세션 관리 (`SessionLocal`, `get_db`)
- 모델 정의 (SQLAlchemy Model vs Pydantic Schema 분리)
- CRUD 함수 작성
- Alembic을 이용한 DB 마이그레이션

### 3.2 비동기 DB (선택)
- `SQLAlchemy 2.0` + `asyncpg`
- `async session` 사용법
- 동기 vs 비동기 DB 드라이버 비교

### 3.3 NoSQL 연동 (선택)
- MongoDB + `motor` (비동기 드라이버)
- Redis 연동 (캐싱 용도)

---

## Phase 4: 인증과 보안

### 4.1 OAuth2 + JWT 인증
- OAuth2 Password Flow 이해
- JWT 토큰 생성 및 검증 (`python-jose`)
- 비밀번호 해싱 (`passlib`, `bcrypt`)
- 로그인 -> 토큰 발급 -> 보호된 엔드포인트 접근 흐름 구현

### 4.2 권한 관리
- 사용자 역할(Role) 기반 접근 제어
- Scopes를 활용한 세분화된 권한
- API Key 인증 방식

### 4.3 보안 베스트 프랙티스
- HTTPS 설정
- Rate Limiting
- Input Sanitization
- 환경변수로 시크릿 관리 (`python-dotenv`, `pydantic-settings`)

---

## Phase 5: 프로젝트 구조화 및 실전 패턴

### 5.1 프로젝트 구조 설계
- 라우터 분리 (`APIRouter`)
- 계층 구조 설계:
  ```
  app/
  ├── main.py
  ├── core/
  │   ├── config.py
  │   └── security.py
  ├── api/
  │   ├── v1/
  │   │   ├── endpoints/
  │   │   │   ├── users.py
  │   │   │   └── items.py
  │   │   └── router.py
  ├── models/
  │   └── user.py
  ├── schemas/
  │   └── user.py
  ├── crud/
  │   └── user.py
  └── db/
      └── session.py
  ```
- 설정 관리 (`BaseSettings`로 환경별 설정)

### 5.2 테스트
- `TestClient`를 활용한 API 테스트
- `pytest` + `httpx.AsyncClient` 비동기 테스트
- 의존성 오버라이드 (DB 모킹 등)
- 테스트 픽스처 구성

### 5.3 백그라운드 작업
- `BackgroundTasks`로 비동기 후처리
- Celery 연동 (무거운 작업 큐잉)
- (실습) 이미지 업로드 후 백그라운드에서 모델 추론 실행

### 5.4 WebSocket
- WebSocket 엔드포인트 구현
- 실시간 통신 패턴 (채팅, 알림)
- (실습) 모델 추론 진행 상황 실시간 스트리밍

---

## Phase 6: 배포 및 운영

### 6.1 Docker 컨테이너화
- Dockerfile 작성 (멀티스테이지 빌드)
- docker-compose로 앱 + DB 구성
- GPU 컨테이너 설정 (딥러닝 모델 서빙 시)

### 6.2 성능 최적화
- Gunicorn + Uvicorn 워커 구성
- 응답 캐싱 전략
- 프로파일링 및 병목 분석

### 6.3 로깅 & 모니터링
- `logging` 모듈 설정
- 구조화된 로깅 (JSON 로그)
- Prometheus + Grafana 메트릭 수집 (선택)
- Health Check 엔드포인트

### 6.4 API 문서화 및 버전 관리
- OpenAPI 스키마 커스터마이징
- API 버전 관리 전략 (`/api/v1/`, `/api/v2/`)
- Tags, Description을 활용한 문서 정리

---

## 실전 프로젝트 제안

학습한 내용을 종합하여 아래 프로젝트 중 하나를 구현해보세요.

### 프로젝트 A: ML 모델 서빙 API
딥러닝 개발자에게 가장 실용적인 프로젝트입니다.
- 이미지 업로드 -> 모델 추론 -> 결과 반환
- JWT 인증으로 API 접근 제어
- 백그라운드 작업으로 배치 추론
- WebSocket으로 추론 진행률 스트리밍
- Redis 캐싱으로 중복 추론 방지
- Docker + GPU 컨테이너 배포

### 프로젝트 B: RESTful CRUD 서비스
웹 백엔드 전반을 익히기 좋은 프로젝트입니다.
- 사용자 관리 (회원가입, 로그인, 프로필)
- 게시판 CRUD + 페이지네이션
- 파일 첨부 기능
- 역할 기반 권한 관리
- 테스트 코드 작성
- Docker Compose 배포

---

## 추천 학습 자료

| 자료 | 링크 |
|------|------|
| FastAPI 공식 문서 | https://fastapi.tiangolo.com |
| FastAPI 공식 튜토리얼 | https://fastapi.tiangolo.com/tutorial/ |
| Pydantic V2 문서 | https://docs.pydantic.dev |
| SQLAlchemy 문서 | https://docs.sqlalchemy.org |
| TestDriven.io FastAPI | https://testdriven.io/blog/topics/fastapi/ |

---

## 학습 팁

1. **공식 문서를 교과서처럼 활용하세요.** FastAPI 공식 문서는 튜토리얼 형식으로 매우 잘 작성되어 있습니다.
2. **Phase별로 작은 프로젝트를 직접 만들어보세요.** 읽기만 하면 금방 잊습니다.
3. **딥러닝 경험을 살려서 모델 서빙 API를 만들어보는 것을 권장합니다.** 익숙한 도메인에서 시작하면 학습이 빠릅니다.
4. **Phase 1~2는 순서대로, Phase 3~6은 필요에 따라 선택적으로** 학습해도 됩니다.
