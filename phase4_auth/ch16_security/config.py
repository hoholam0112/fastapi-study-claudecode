"""
Chapter 16: 보안 강화 - 설정 관리 모듈

pydantic-settings를 사용하여 환경변수를 안전하게 관리한다.
- .env 파일 또는 시스템 환경변수에서 설정을 로드
- 타입 검증을 통한 설정 값 안전성 보장
- lru_cache를 통한 설정 인스턴스 캐싱
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스.

    환경변수 또는 .env 파일에서 값을 로드한다.
    환경변수가 없으면 각 필드의 기본값을 사용한다.
    """

    # ── 기본 애플리케이션 설정 ──
    APP_NAME: str = "FastAPI 보안 예제"        # 애플리케이션 이름
    DEBUG: bool = False                        # 디버그 모드 활성화 여부

    # ── 보안 관련 설정 ──
    SECRET_KEY: str = "changeme-development-secret-key-not-for-production"  # JWT 서명 비밀 키
    API_KEY: str = "changeme-secret-api-key"   # API Key 인증에 사용할 키

    # ── 데이터베이스 설정 ──
    DATABASE_URL: str = "sqlite:///./app.db"   # 데이터베이스 연결 URL

    # ── CORS 설정 ──
    ALLOWED_ORIGINS: list[str] = [             # CORS에서 허용할 출처 목록
        "http://localhost:3000",               # React 개발 서버
        "http://localhost:8080",               # Vue 개발 서버
        "http://127.0.0.1:8000",               # FastAPI 자체 (Swagger UI)
    ]

    # ── Rate Limiting 설정 ──
    RATE_LIMIT_REQUESTS: int = 10              # 제한 시간 내 최대 요청 횟수
    RATE_LIMIT_WINDOW_SECONDS: int = 60        # Rate Limit 시간 창 (초)

    # ── pydantic-settings 모델 설정 ──
    model_config = SettingsConfigDict(
        env_file=".env",                       # .env 파일 경로
        env_file_encoding="utf-8",             # .env 파일 인코딩
        case_sensitive=True,                   # 환경변수 이름 대소문자 구분
        extra="ignore",                        # 정의되지 않은 환경변수 무시
    )


@lru_cache()
def get_settings() -> Settings:
    """
    설정 인스턴스를 반환하는 함수.

    @lru_cache 데코레이터를 사용하여 설정 객체를 한 번만 생성하고 캐싱한다.
    이를 통해 매 요청마다 .env 파일을 다시 읽는 오버헤드를 방지한다.

    FastAPI의 Depends()와 함께 사용하면 의존성 주입을 통해
    어디서든 설정에 접근할 수 있다.
    """
    return Settings()
