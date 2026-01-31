# FastAPI Study

> Python 개발자를 위한 FastAPI 학습 프로젝트
> 딥러닝 개발자 -> FastAPI 중급자 수준 도달을 목표로 합니다.

## 프로젝트 구조

```
fastapi-study-claudecode/
├── CURRICULUM.md                # 전체 학습 커리큘럼
├── requirements.txt             # 전역 의존성
│
├── phase1_basics/               # Phase 1: FastAPI 입문
│   ├── ch01_setup/              # 개요 및 환경 세팅
│   ├── ch02_path_query_params/  # Path & Query Parameters
│   ├── ch03_request_body/       # Request Body와 Pydantic
│   ├── ch04_response/           # Response 다루기
│   └── ch05_crud/               # CRUD API 실습
│
├── phase2_core/                 # Phase 2: 핵심 기능
│   ├── ch06_dependency_injection/  # 의존성 주입
│   ├── ch07_async/              # 비동기 처리 (async/await)
│   ├── ch08_error_handling/     # 에러 핸들링
│   ├── ch09_middleware/         # 미들웨어 & CORS
│   └── ch10_file_upload/        # Form Data & File Upload
│
├── phase3_database/             # Phase 3: 데이터베이스 연동
│   ├── ch11_sqlalchemy/         # SQLAlchemy + FastAPI
│   ├── ch12_async_db/           # 비동기 DB
│   └── ch13_nosql/              # NoSQL (MongoDB, Redis)
│
├── phase4_auth/                 # Phase 4: 인증과 보안
│   ├── ch14_jwt_auth/           # OAuth2 + JWT 인증
│   ├── ch15_permissions/        # 권한 관리
│   └── ch16_security/           # 보안 베스트 프랙티스
│
├── phase5_patterns/             # Phase 5: 프로젝트 구조화 및 실전 패턴
│   ├── ch17_project_structure/  # 프로젝트 구조 설계
│   ├── ch18_testing/            # 테스트 (pytest)
│   ├── ch19_background_tasks/   # 백그라운드 작업
│   └── ch20_websocket/          # WebSocket
│
├── phase6_deployment/           # Phase 6: 배포 및 운영
│   ├── ch21_docker/             # Docker 컨테이너화
│   ├── ch22_performance/        # 성능 최적화
│   ├── ch23_logging/            # 로깅 & 모니터링
│   └── ch24_api_docs/           # API 문서화 및 버전 관리
│
└── projects/                    # 캡스톤 프로젝트
    ├── ml_serving_api/          # 프로젝트 A: ML 모델 서빙 API
    └── restful_crud_service/    # 프로젝트 B: RESTful CRUD 서비스
```

## 학습 로드맵

| Phase | 주제 | 챕터 | 비고 |
|-------|------|------|------|
| Phase 1 | FastAPI 입문 | Ch01 ~ Ch05 | 필수 |
| Phase 2 | 핵심 기능 | Ch06 ~ Ch10 | 필수 |
| Phase 3 | 데이터베이스 연동 | Ch11 ~ Ch13 | 선택 |
| Phase 4 | 인증과 보안 | Ch14 ~ Ch16 | 선택 |
| Phase 5 | 프로젝트 구조화 | Ch17 ~ Ch20 | 선택 |
| Phase 6 | 배포 및 운영 | Ch21 ~ Ch24 | 선택 |

- Phase 1~2는 순서대로 학습
- Phase 3~6은 필요에 따라 선택적으로 학습 가능

## 시작하기

### 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 첫 번째 앱 실행

```bash
cd phase1_basics/ch01_setup
uvicorn main:app --reload
```

브라우저에서 확인:
- API 문서 (Swagger UI): http://127.0.0.1:8000/docs
- API 문서 (ReDoc): http://127.0.0.1:8000/redoc

## 기술 스택

- **Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn
- **Validation**: Pydantic V2
- **ORM**: SQLAlchemy 2.0
- **Auth**: python-jose (JWT), passlib (bcrypt)
- **Testing**: pytest, pytest-asyncio
- **Deployment**: Docker, Gunicorn

## 캡스톤 프로젝트

### 프로젝트 A: ML 모델 서빙 API

딥러닝 모델 추론을 위한 프로덕션 레벨 API 서비스

- JWT 인증, 단건/배치 추론, 모델 메타데이터 관리
- Docker 컨테이너 배포

### 프로젝트 B: RESTful CRUD 서비스

블로그/게시판 형태의 완전한 REST API 서비스

- 사용자 관리, 게시글 CRUD, 페이지네이션, 검색/필터링
- 역할 기반 권한 관리, pytest 테스트, PostgreSQL 연동

## 참고 자료

| 자료 | 링크 |
|------|------|
| FastAPI 공식 문서 | https://fastapi.tiangolo.com |
| FastAPI 튜토리얼 | https://fastapi.tiangolo.com/tutorial/ |
| Pydantic V2 문서 | https://docs.pydantic.dev |
| SQLAlchemy 문서 | https://docs.sqlalchemy.org |
