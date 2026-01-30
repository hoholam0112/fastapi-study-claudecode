# Chapter 01 - FastAPI 소개 및 환경 세팅

## 학습 목표

- FastAPI가 무엇인지 이해하고, 기존 프레임워크(Flask, Django)와의 차이를 파악한다.
- Python 가상환경을 구성하고 FastAPI를 설치할 수 있다.
- 첫 번째 FastAPI 앱을 실행하고, 자동 생성되는 API 문서를 확인할 수 있다.

---

## 핵심 개념

### 1. FastAPI란?

FastAPI는 Python 3.7+ 기반의 **현대적이고 고성능인 웹 프레임워크**이다.
표준 Python 타입 힌트를 활용하여 API를 구축하며, 아래와 같은 특징을 갖는다.

- **고성능**: Node.js, Go와 대등한 수준의 성능 (Starlette + Uvicorn 기반)
- **빠른 개발 속도**: 기능 개발 속도 약 200~300% 향상 (공식 문서 기준)
- **적은 버그**: 타입 힌트 기반 자동 검증으로 휴먼 에러 감소
- **자동 문서화**: Swagger UI(`/docs`)와 ReDoc(`/redoc`) 자동 생성
- **표준 기반**: OpenAPI, JSON Schema 완벽 호환

### 2. Flask / Django / FastAPI 비교

| 항목 | Flask | Django | FastAPI |
|------|-------|--------|---------|
| **유형** | 마이크로 프레임워크 | 풀스택 프레임워크 | 마이크로 프레임워크 (API 특화) |
| **비동기 지원** | 제한적 (Flask 2.0+) | 제한적 (Django 3.1+) | 네이티브 async/await |
| **성능** | 보통 | 보통 | 매우 높음 (Starlette 기반) |
| **타입 힌트 활용** | 없음 | 없음 | 핵심 기능 (Pydantic 통합) |
| **자동 API 문서** | 없음 (별도 확장 필요) | 없음 (DRF + drf-yasg 필요) | 기본 내장 (Swagger UI, ReDoc) |
| **데이터 검증** | 수동 (WTForms 등) | Django Forms / DRF Serializer | Pydantic 자동 검증 |
| **ORM** | SQLAlchemy (선택) | Django ORM (내장) | SQLAlchemy / Tortoise (선택) |
| **학습 곡선** | 낮음 | 높음 | 보통 (Python 타입 힌트 필요) |
| **적합한 용도** | 소규모 웹앱, 프로토타입 | 대규모 웹 서비스 | REST API, 마이크로서비스 |
| **커뮤니티 규모** | 매우 큼 | 매우 큼 | 빠르게 성장 중 |

### 3. 자동 API 문서

FastAPI는 코드만 작성하면 아래 두 가지 API 문서를 **자동으로 생성**한다.

| 경로 | 문서 종류 | 설명 |
|------|----------|------|
| `/docs` | **Swagger UI** | 대화형 API 문서. 브라우저에서 직접 API 호출 테스트 가능 |
| `/redoc` | **ReDoc** | 읽기 전용 API 문서. 깔끔한 레이아웃으로 문서 공유에 적합 |

두 문서 모두 **OpenAPI 스펙**(JSON)을 기반으로 자동 생성되며, `/openapi.json` 경로에서 원본 스펙을 확인할 수 있다.

---

## 환경 세팅 가이드

### 1단계: Python 가상환경 생성

```bash
# 프로젝트 루트로 이동
cd fastapi-study

# 가상환경 생성 (Python 3.7 이상 필요)
python -m venv venv

# 가상환경 활성화
# macOS / Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### 2단계: 패키지 설치

```bash
# FastAPI 설치
pip install fastapi

# ASGI 서버(Uvicorn) 설치
pip install "uvicorn[standard]"

# 또는 한 번에 설치
pip install fastapi "uvicorn[standard]"
```

### 3단계: 설치 확인

```bash
pip list | grep -i fastapi
pip list | grep -i uvicorn
```

---

## 코드 실행 방법

```bash
# ch01_setup 디렉토리로 이동
cd phase1_basics/ch01_setup

# 개발 서버 실행 (자동 리로드 활성화)
uvicorn main:app --reload

# 특정 포트 지정 시
uvicorn main:app --reload --port 8001
```

서버 실행 후 아래 주소에 접속하여 확인한다.

| URL | 설명 |
|-----|------|
| http://127.0.0.1:8000 | 루트 엔드포인트 |
| http://127.0.0.1:8000/hello/홍길동 | 이름을 포함한 인사 |
| http://127.0.0.1:8000/health | 서버 상태 확인 |
| http://127.0.0.1:8000/docs | Swagger UI 문서 |
| http://127.0.0.1:8000/redoc | ReDoc 문서 |

---

## 실습 포인트

1. **서버 실행 후 `/docs`에 접속**하여 Swagger UI에서 각 엔드포인트를 직접 호출해 본다.
2. **`/hello/{name}`** 경로에 한글 이름을 넣어 보고 정상 동작하는지 확인한다.
3. `--reload` 옵션의 효과를 확인하기 위해, 서버를 켜둔 상태에서 `main.py` 코드를 수정하고 저장한 뒤 브라우저를 새로고침해 본다.
4. `/openapi.json` 경로에 접속하여 자동 생성된 OpenAPI 스펙(JSON)의 구조를 살펴본다.
5. 새로운 엔드포인트를 하나 추가해 보고(예: `/goodbye/{name}`), `/docs`에 자동 반영되는 것을 확인한다.
