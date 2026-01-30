# RESTful CRUD 서비스

## 프로젝트 개요

완전한 RESTful CRUD(Create, Read, Update, Delete) 서비스를 구현하는 프로젝트입니다.
게시판/블로그 형태의 API를 구축하며, 페이지네이션, 검색/필터링, 사용자 인증,
데이터베이스 마이그레이션 등 실무에서 필수적인 기능들을 모두 포함합니다.

## 주요 기능

- **CRUD 작업**: 게시글의 생성, 조회, 수정, 삭제 API
- **페이지네이션**: 대량의 데이터를 페이지 단위로 조회
- **검색 및 필터링**: 키워드 검색, 카테고리 필터, 정렬 기능
- **사용자 인증**: JWT 기반 회원가입, 로그인, 권한 관리
- **데이터베이스**: SQLAlchemy ORM과 Alembic 마이그레이션
- **테스트**: pytest를 활용한 단위 테스트 및 통합 테스트

## 기술 스택

| 기술 | 용도 |
|------|------|
| **FastAPI** | 웹 프레임워크 |
| **Pydantic** | 데이터 검증 및 직렬화 |
| **SQLAlchemy** | ORM (데이터베이스 모델링) |
| **Alembic** | 데이터베이스 마이그레이션 |
| **python-jose** | JWT 토큰 생성 및 검증 |
| **passlib / bcrypt** | 비밀번호 해싱 |
| **pytest** | 테스트 프레임워크 |
| **Docker** | 컨테이너화 및 배포 |
| **PostgreSQL** | 관계형 데이터베이스 |

## 디렉토리 구조

```
restful_crud_service/
├── README.md                    # 프로젝트 설명서 (현재 파일)
├── requirements.txt             # Python 패키지 의존성
├── Dockerfile                   # Docker 빌드 파일
├── docker-compose.yml           # Docker Compose 설정 (웹 + DB)
└── app/
    ├── __init__.py
    ├── main.py                  # FastAPI 앱 진입점
    ├── core/
    │   └── __init__.py          # 설정, 보안, DB 연결 등 핵심 모듈
    ├── api/
    │   └── __init__.py          # API 라우터 및 엔드포인트
    ├── models/
    │   └── __init__.py          # SQLAlchemy ORM 모델
    ├── schemas/
    │   └── __init__.py          # Pydantic 요청/응답 스키마
    └── crud/
        └── __init__.py          # CRUD 비즈니스 로직
```

## 구현 가이드

이 프로젝트는 Phase 1~4를 모두 학습한 후 도전하는 것을 권장합니다.
각 기능 구현 시 참고해야 할 챕터는 다음과 같습니다:

| 구현 항목 | 참고 Phase / 챕터 |
|-----------|-------------------|
| FastAPI 앱 기본 구조 | Phase 1 - FastAPI 기초, 라우팅 |
| Pydantic 스키마 설계 | Phase 1 - Pydantic 모델, 요청/응답 처리 |
| CRUD 엔드포인트 구현 | Phase 1 - HTTP 메서드, 경로 매개변수, 쿼리 매개변수 |
| SQLAlchemy 모델 정의 | Phase 2 - 데이터베이스 연동 (SQLAlchemy) |
| Alembic 마이그레이션 | Phase 2 - 데이터베이스 마이그레이션 |
| JWT 인증 구현 | Phase 2 - 보안 및 인증 (OAuth2, JWT) |
| 의존성 주입 활용 | Phase 2 - 의존성 주입 시스템 |
| 페이지네이션 구현 | Phase 2 - 쿼리 매개변수 활용, 의존성 주입 |
| 에러 처리 및 로깅 | Phase 3 - 에러 핸들링, 미들웨어 |
| 비동기 DB 처리 | Phase 3 - 비동기 프로그래밍 |
| 테스트 작성 | Phase 4 - 테스트 전략 (pytest, TestClient) |
| Docker 배포 | Phase 4 - 배포 및 컨테이너화 |

## API 엔드포인트 목록

### 인증 (Auth)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/auth/register` | 회원가입 |
| `POST` | `/api/v1/auth/login` | 로그인 (JWT 토큰 발급) |
| `GET` | `/api/v1/auth/me` | 현재 사용자 정보 조회 |

### 게시글 (Posts)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/posts` | 게시글 생성 |
| `GET` | `/api/v1/posts` | 게시글 목록 조회 (페이지네이션, 검색, 필터) |
| `GET` | `/api/v1/posts/{post_id}` | 게시글 상세 조회 |
| `PUT` | `/api/v1/posts/{post_id}` | 게시글 수정 |
| `DELETE` | `/api/v1/posts/{post_id}` | 게시글 삭제 |

### 댓글 (Comments) - 선택 구현

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/posts/{post_id}/comments` | 댓글 작성 |
| `GET` | `/api/v1/posts/{post_id}/comments` | 댓글 목록 조회 |
| `DELETE` | `/api/v1/comments/{comment_id}` | 댓글 삭제 |

### 시스템

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/health` | 서비스 헬스 체크 |

## 실행 방법

### 로컬 실행

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 데이터베이스 마이그레이션 (Alembic 설정 후)
alembic upgrade head

# 4. 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. API 문서 확인
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### Docker 실행

```bash
# Docker Compose로 웹 서버 + PostgreSQL 함께 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up --build -d

# 종료
docker-compose down

# 볼륨 포함 종료 (DB 데이터 삭제)
docker-compose down -v
```

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 상세 출력으로 실행
pytest -v

# 특정 테스트 파일 실행
pytest tests/test_posts.py

# 커버리지 리포트 생성
pytest --cov=app --cov-report=html
```
