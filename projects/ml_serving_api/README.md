# ML 모델 서빙 API

## 프로젝트 개요

ML(머신러닝) 모델을 REST API로 서빙하는 서비스입니다.
학습된 모델을 로드하여 실시간 추론 요청을 처리하고, 배치 예측 기능과 JWT 기반 인증을 제공합니다.
FastAPI의 비동기 처리 능력을 활용하여 고성능 모델 서빙 환경을 구축하는 것이 목표입니다.

## 주요 기능

- **모델 추론 API**: 단건 예측 요청을 처리하는 REST 엔드포인트
- **배치 처리**: 여러 건의 데이터를 한 번에 예측하는 배치 추론 API
- **JWT 인증**: JSON Web Token 기반 사용자 인증 및 권한 관리
- **모델 정보 조회**: 현재 로드된 모델의 메타데이터 조회
- **Health Check**: 서비스 상태 및 모델 로딩 상태 확인

## 기술 스택

| 기술 | 용도 |
|------|------|
| **FastAPI** | 웹 프레임워크 |
| **Pydantic** | 데이터 검증 및 직렬화 |
| **scikit-learn** | ML 모델 학습 및 추론 |
| **python-jose** | JWT 토큰 생성 및 검증 |
| **passlib / bcrypt** | 비밀번호 해싱 |
| **Docker** | 컨테이너화 및 배포 |
| **uvicorn** | ASGI 서버 |

## 디렉토리 구조

```
ml_serving_api/
├── README.md                    # 프로젝트 설명서 (현재 파일)
├── requirements.txt             # Python 패키지 의존성
├── Dockerfile                   # Docker 빌드 파일
├── docker-compose.yml           # Docker Compose 설정
└── app/
    ├── __init__.py
    ├── main.py                  # FastAPI 앱 진입점
    ├── core/
    │   ├── __init__.py
    │   ├── config.py            # 환경 설정 (Settings)
    │   └── security.py          # JWT 인증 로직
    ├── api/
    │   ├── __init__.py
    │   └── v1/
    │       ├── __init__.py
    │       ├── router.py        # API v1 라우터 통합
    │       └── endpoints/
    │           ├── __init__.py
    │           ├── auth.py      # 인증 엔드포인트
    │           └── inference.py # 추론 엔드포인트
    ├── models/
    │   └── __init__.py          # DB/도메인 모델 (필요 시)
    ├── schemas/
    │   └── __init__.py          # Pydantic 스키마 정의
    └── services/
        ├── __init__.py
        └── ml_service.py        # ML 모델 로딩 및 추론 서비스
```

## 구현 가이드

이 프로젝트는 Phase 1~4를 모두 학습한 후 도전하는 것을 권장합니다.
각 기능 구현 시 참고해야 할 챕터는 다음과 같습니다:

| 구현 항목 | 참고 Phase / 챕터 |
|-----------|-------------------|
| FastAPI 앱 기본 구조 | Phase 1 - FastAPI 기초, 라우팅 |
| Pydantic 스키마 설계 | Phase 1 - Pydantic 모델, 요청/응답 처리 |
| JWT 인증 구현 | Phase 2 - 보안 및 인증 (OAuth2, JWT) |
| 의존성 주입 활용 | Phase 2 - 의존성 주입 시스템 |
| 비동기 처리 | Phase 3 - 비동기 프로그래밍 |
| 에러 처리 및 로깅 | Phase 3 - 에러 핸들링, 미들웨어 |
| Docker 배포 | Phase 4 - 배포 및 컨테이너화 |
| 테스트 작성 | Phase 4 - 테스트 전략 |

## API 엔드포인트 목록

### 인증 (Auth)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/auth/token` | JWT 액세스 토큰 발급 |

### 추론 (Inference)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/predict` | 단건 모델 추론 요청 |
| `POST` | `/api/v1/batch-predict` | 배치 모델 추론 요청 |
| `GET` | `/api/v1/model/info` | 현재 모델 정보 조회 |

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

# 3. 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. API 문서 확인
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### Docker 실행

```bash
# Docker Compose로 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up --build -d

# 종료
docker-compose down
```
