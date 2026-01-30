"""
Gunicorn 설정 파일 (gunicorn.conf.py)
======================================
Gunicorn + Uvicorn 워커 조합으로 FastAPI를 프로덕션 환경에서 실행하기 위한 설정.

실행 방법:
    gunicorn -c gunicorn.conf.py main:app

참고: Uvicorn만 사용할 경우 (개발용):
    uvicorn main:app --reload
"""

import multiprocessing
import os

# ============================================================
# 서버 소켓 설정
# ============================================================

# 바인드 주소와 포트
# 0.0.0.0으로 설정하면 모든 네트워크 인터페이스에서 접속을 허용한다
# Docker 컨테이너 내부에서 실행할 때는 반드시 0.0.0.0을 사용해야 한다
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# ============================================================
# 워커 프로세스 설정
# ============================================================

# 워커 수 계산: (CPU 코어 수 × 2) + 1
# 이 공식은 I/O 바운드 작업에 최적화된 경험적 수치이다
# CPU 바운드 작업이 많다면 코어 수와 동일하게 설정하는 것이 좋다
# 환경변수로 직접 지정할 수도 있다
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# 워커 클래스: Uvicorn의 비동기 워커를 사용한다
# FastAPI는 ASGI 프레임워크이므로 반드시 ASGI 호환 워커를 사용해야 한다
worker_class = "uvicorn.workers.UvicornWorker"

# 워커당 스레드 수 (UvicornWorker에서는 이벤트 루프를 사용하므로 1로 설정)
threads = 1

# ============================================================
# 타임아웃 설정
# ============================================================

# 워커 타임아웃 (초)
# 워커가 이 시간 내에 응답하지 않으면 Gunicorn이 워커를 강제 종료하고 재시작한다
# 무거운 연산이나 느린 외부 API 호출이 있다면 값을 늘려야 한다
timeout = 120

# Graceful 타임아웃 (초)
# 워커를 종료할 때 진행 중인 요청이 완료될 때까지 대기하는 시간
graceful_timeout = 30

# Keep-Alive 타임아웃 (초)
# 클라이언트와의 연결을 유지하는 시간
# 리버스 프록시(Nginx 등) 뒤에서 실행할 때는 프록시의 설정보다 길게 설정한다
keepalive = 5

# ============================================================
# 로깅 설정
# ============================================================

# 접근 로그 파일 경로
# "-"로 설정하면 표준 출력(stdout)으로 로그를 출력한다
# Docker 환경에서는 stdout으로 출력하여 docker logs로 확인하는 것이 권장된다
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")

# 에러 로그 파일 경로
# "-"로 설정하면 표준 에러(stderr)로 출력한다
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")

# 로그 레벨: debug, info, warning, error, critical
# 프로덕션에서는 info 또는 warning을 권장한다
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# 접근 로그 형식
# 요청 메서드, URL, 상태 코드, 응답 시간 등을 기록한다
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# ============================================================
# 프로세스 관리 설정
# ============================================================

# 워커가 일정 요청 수를 처리한 후 재시작되도록 설정한다
# 메모리 누수 방지에 도움이 된다 (0이면 비활성화)
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))

# max_requests에 랜덤 지터를 추가하여 모든 워커가 동시에 재시작되는 것을 방지한다
# 예: max_requests=1000, max_requests_jitter=50이면
#     각 워커는 950~1050 요청 사이의 랜덤한 시점에 재시작된다
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "50"))

# 데몬 모드 (백그라운드 실행)
# Docker 컨테이너에서는 False여야 컨테이너가 종료되지 않는다
daemon = False

# 마스터 프로세스의 PID 파일 경로 (선택사항)
# 프로세스 관리 도구(systemd 등)와 연동할 때 사용한다
# pidfile = "/var/run/gunicorn.pid"

# ============================================================
# 보안 설정
# ============================================================

# 요청 본문의 최대 크기 (바이트)
# 대용량 파일 업로드가 필요하면 값을 늘린다 (0이면 무제한)
limit_request_body = int(os.getenv("GUNICORN_MAX_BODY_SIZE", str(10 * 1024 * 1024)))  # 기본 10MB

# 요청 헤더의 최대 크기 (바이트)
limit_request_field_size = 8190

# 요청 헤더의 최대 개수
limit_request_fields = 100

# ============================================================
# 서버 훅 (이벤트 콜백)
# ============================================================

def on_starting(server):
    """Gunicorn 마스터 프로세스가 시작될 때 호출된다."""
    print(f"[Gunicorn] 서버 시작 중... (바인드: {bind}, 워커: {workers}개)")


def on_reload(server):
    """설정 파일이 변경되어 서버가 리로드될 때 호출된다."""
    print("[Gunicorn] 설정이 변경되어 서버를 리로드합니다.")


def post_fork(server, worker):
    """새로운 워커 프로세스가 생성된 후 호출된다."""
    print(f"[Gunicorn] 워커 #{worker.pid} 시작됨")


def pre_exec(server):
    """새로운 마스터 프로세스가 fork되기 직전에 호출된다."""
    print("[Gunicorn] 마스터 프로세스를 새로 시작합니다.")


def worker_exit(server, worker):
    """워커 프로세스가 종료될 때 호출된다."""
    print(f"[Gunicorn] 워커 #{worker.pid} 종료됨")
