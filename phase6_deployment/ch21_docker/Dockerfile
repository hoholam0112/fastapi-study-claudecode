# ============================================================
# 멀티스테이지 빌드를 활용한 FastAPI Dockerfile
# ============================================================
# 스테이지 1(builder): 의존성 설치를 전담한다
# 스테이지 2(production): 실행에 필요한 파일만 복사하여 이미지 크기를 최소화한다
# ============================================================

# ----------------------------------------------------------
# 스테이지 1: 빌드 스테이지 (의존성 설치)
# ----------------------------------------------------------
# 전체 Python 이미지를 사용하여 C 확장 모듈도 컴파일할 수 있도록 한다
FROM python:3.11-slim AS builder

# 시스템 의존성 설치 (빌드에 필요한 패키지)
# gcc 등 컴파일 도구가 필요한 경우를 대비한다
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일만 먼저 복사하여 Docker 레이어 캐시를 활용한다
# requirements.txt가 변경되지 않으면 이 레이어는 캐시에서 재사용된다
COPY requirements.txt .

# --user 옵션으로 사용자 디렉토리에 패키지를 설치한다
# 이렇게 하면 다음 스테이지에서 해당 디렉토리만 복사할 수 있다
RUN pip install --no-cache-dir --user -r requirements.txt

# ----------------------------------------------------------
# 스테이지 2: 실행 스테이지 (프로덕션 이미지)
# ----------------------------------------------------------
# slim 이미지를 사용하여 최종 이미지 크기를 최소화한다
FROM python:3.11-slim AS production

# 보안을 위해 root가 아닌 일반 사용자로 실행한다
# 컨테이너 내부에서 불필요한 권한 상승을 방지한다
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# 작업 디렉토리 설정
WORKDIR /app

# 빌드 스테이지에서 설치된 Python 패키지만 복사한다
# 빌드 도구(gcc 등)는 포함되지 않으므로 이미지가 가벼워진다
COPY --from=builder /root/.local /home/appuser/.local

# PATH에 사용자 패키지 경로를 추가한다
ENV PATH="/home/appuser/.local/bin:${PATH}"

# 환경변수 기본값 설정
# docker run -e 또는 docker-compose의 environment로 덮어쓸 수 있다
ENV APP_NAME="FastAPI Docker 학습" \
    VERSION="1.0.0" \
    ENVIRONMENT="production" \
    DEBUG="false" \
    # Python 출력 버퍼링을 비활성화하여 로그가 즉시 출력되도록 한다
    PYTHONUNBUFFERED=1 \
    # .pyc 파일 생성을 방지하여 이미지 크기를 절약한다
    PYTHONDONTWRITEBYTECODE=1

# 애플리케이션 소스 코드를 복사한다
# .dockerignore 파일로 불필요한 파일(venv, __pycache__ 등)을 제외할 수 있다
COPY . .

# 파일 소유권을 appuser로 변경한다
RUN chown -R appuser:appuser /app

# 일반 사용자로 전환한다
USER appuser

# 컨테이너가 8000번 포트를 사용함을 문서화한다
# 실제 포트 매핑은 docker run -p 또는 docker-compose의 ports에서 설정한다
EXPOSE 8000

# 헬스체크 설정
# 30초마다 /health 엔드포인트를 호출하여 컨테이너 상태를 확인한다
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 컨테이너 시작 시 Uvicorn 서버를 실행한다
# --host 0.0.0.0: 모든 네트워크 인터페이스에서 접속을 허용한다
# --port 8000: 8000번 포트에서 서비스한다
# --workers 1: 단일 워커 (프로덕션에서는 Gunicorn과 함께 사용 권장)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
