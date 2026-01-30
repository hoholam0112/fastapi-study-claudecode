"""
애플리케이션 환경 설정 모듈

pydantic-settings의 BaseSettings를 활용하여
환경변수 및 .env 파일에서 설정값을 자동으로 로드한다.
lru_cache로 설정 객체를 싱글톤처럼 재사용한다.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    애플리케이션 전역 설정 클래스

    환경변수에서 값을 읽어오며, 접두사 "APP_"이 붙은 변수를 자동 매핑한다.
    예: APP_NAME 환경변수 -> Settings.APP_NAME 필드

    Attributes:
        APP_NAME: 애플리케이션 이름
        VERSION: API 버전 문자열
        DEBUG: 디버그 모드 활성화 여부
        DATABASE_URL: 데이터베이스 연결 문자열
    """

    APP_NAME: str = "FastAPI 프로젝트 구조 데모"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./demo.db"

    # pydantic-settings v2 방식의 설정
    # env_prefix: 환경변수 접두사 (APP_APP_NAME, APP_VERSION 등으로 설정 가능)
    # env_file: .env 파일 경로 (프로젝트 루트에 위치)
    # env_file_encoding: .env 파일 인코딩
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 정의되지 않은 환경변수는 무시한다
    )


@lru_cache
def get_settings() -> Settings:
    """
    설정 객체를 반환하는 함수 (캐싱 적용)

    lru_cache 데코레이터를 사용하여 Settings 인스턴스를 한 번만 생성하고,
    이후 호출 시에는 캐시된 객체를 반환한다.
    이렇게 하면 매 요청마다 환경변수를 다시 읽지 않아 성능이 향상된다.

    FastAPI의 Depends()와 함께 의존성으로 주입할 수도 있다:
        @app.get("/")
        async def root(settings: Settings = Depends(get_settings)):
            return {"app_name": settings.APP_NAME}

    Returns:
        Settings: 캐시된 설정 객체
    """
    return Settings()
