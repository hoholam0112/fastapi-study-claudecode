# Chapter 21: Docker를 활용한 FastAPI 배포

## 학습 목표

1. Docker의 기초 개념과 컨테이너 가상화 원리를 이해한다
2. FastAPI 애플리케이션을 위한 최적화된 Dockerfile을 작성할 수 있다
3. docker-compose를 활용하여 다중 서비스 환경을 구성할 수 있다
4. 멀티스테이지 빌드를 통해 이미지 크기를 최소화할 수 있다
5. 환경변수를 안전하게 관리하는 방법을 익힌다

---

## 핵심 개념

### 1. Docker 기초

Docker는 애플리케이션을 **컨테이너**라는 격리된 환경에서 실행하는 플랫폼이다.

| 개념 | 설명 |
|------|------|
| **이미지(Image)** | 컨테이너를 생성하기 위한 읽기 전용 템플릿. Dockerfile로 정의한다 |
| **컨테이너(Container)** | 이미지의 실행 인스턴스. 격리된 프로세스 환경을 제공한다 |
| **레지스트리(Registry)** | 이미지를 저장하고 배포하는 저장소 (예: Docker Hub, AWS ECR) |
| **볼륨(Volume)** | 컨테이너의 데이터를 영속적으로 저장하는 메커니즘 |
| **네트워크(Network)** | 컨테이너 간 통신을 위한 가상 네트워크 |

### 2. Dockerfile 작성법

Dockerfile은 이미지를 빌드하기 위한 명령어 집합이다. 주요 명령어는 다음과 같다:

```dockerfile
FROM        # 베이스 이미지 지정
WORKDIR     # 작업 디렉토리 설정
COPY        # 파일 복사
RUN         # 빌드 시 명령어 실행
ENV         # 환경변수 설정
EXPOSE      # 노출할 포트 선언
CMD         # 컨테이너 시작 시 실행할 명령어
```

**레이어 캐시 최적화 원칙**: 변경 빈도가 낮은 명령어를 먼저 배치한다. `requirements.txt`를 먼저 복사하고 의존성을 설치한 뒤, 소스 코드를 복사하면 코드 변경 시 의존성 설치 레이어를 재사용할 수 있다.

### 3. 멀티스테이지 빌드

멀티스테이지 빌드는 빌드 도구와 런타임 환경을 분리하여 최종 이미지 크기를 줄이는 기법이다.

```dockerfile
# 빌드 스테이지: 의존성 설치 및 컴파일
FROM python:3.11 AS builder
RUN pip install --user -r requirements.txt

# 실행 스테이지: 필요한 파일만 복사
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

### 4. docker-compose 활용

docker-compose는 여러 컨테이너를 하나의 YAML 파일로 정의하고 관리하는 도구이다. 웹 서버, 데이터베이스, 캐시 등 여러 서비스를 한 번에 실행할 수 있다.

### 5. 환경변수 관리

| 방법 | 용도 | 보안 수준 |
|------|------|-----------|
| `ENV` (Dockerfile) | 빌드 시 기본값 설정 | 낮음 (이미지에 포함됨) |
| `environment` (docker-compose) | 서비스별 환경변수 | 중간 |
| `.env` 파일 | 로컬 개발용 변수 모음 | 중간 (`.gitignore`에 추가 필수) |
| Docker Secrets | 프로덕션 비밀 정보 | 높음 |

---

## 빌드 및 실행 방법

### 로컬 실행 (개발용)

```bash
# 의존성 설치
pip install fastapi uvicorn

# 서버 실행
uvicorn main:app --reload

# 환경변수와 함께 실행
APP_NAME="Docker학습" VERSION="1.0.0" uvicorn main:app --reload
```

### Docker로 실행

```bash
# 이미지 빌드
docker build -t fastapi-docker-study .

# 컨테이너 실행
docker run -d -p 8000:8000 --name fastapi-app fastapi-docker-study

# 환경변수를 지정하여 실행
docker run -d -p 8000:8000 \
  -e APP_NAME="Docker학습앱" \
  -e VERSION="2.0.0" \
  --name fastapi-app fastapi-docker-study

# 로그 확인
docker logs -f fastapi-app

# 컨테이너 중지 및 삭제
docker stop fastapi-app && docker rm fastapi-app
```

### docker-compose로 실행

```bash
# 서비스 시작 (백그라운드)
docker-compose up -d

# 서비스 시작 (로그 출력)
docker-compose up

# 이미지 재빌드 후 시작
docker-compose up --build

# 서비스 중지
docker-compose down

# 볼륨까지 포함하여 정리
docker-compose down -v
```

### 유용한 Docker 명령어

```bash
# 실행 중인 컨테이너 목록
docker ps

# 이미지 목록 및 크기 확인
docker images

# 컨테이너 내부 접속
docker exec -it fastapi-app /bin/bash

# 불필요한 리소스 정리
docker system prune -a
```

---

## 실습 포인트

1. **Dockerfile 레이어 캐시 실험**: `requirements.txt`를 변경하지 않고 `main.py`만 수정한 뒤 다시 빌드하여 캐시가 활용되는 것을 확인한다
2. **멀티스테이지 빌드 비교**: 단일 스테이지와 멀티스테이지 빌드의 이미지 크기를 `docker images`로 비교한다
3. **환경변수 주입**: `docker run -e`와 `docker-compose.yml`의 `environment`를 통해 환경변수를 변경하고 `/info` 엔드포인트에서 확인한다
4. **볼륨 마운트 개발**: docker-compose의 볼륨 마운트를 활용하여 코드 변경이 실시간 반영되는 개발 환경을 구성한다
5. **헬스체크 구현**: Docker의 `HEALTHCHECK` 명령어와 `/health` 엔드포인트를 연동하여 컨테이너 상태 모니터링을 구현한다

---

## 프로젝트 구조

```
ch21_docker/
├── README.md              # 학습 가이드 (현재 문서)
├── main.py                # FastAPI 애플리케이션
├── Dockerfile             # 멀티스테이지 Docker 빌드 파일
├── docker-compose.yml     # 다중 서비스 구성 파일
└── requirements.txt       # Python 의존성 목록 (필요 시 생성)
```
