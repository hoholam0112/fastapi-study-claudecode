"""
애플리케이션 설정 모듈

환경 변수 기반의 설정 관리를 구현합니다.
"""

# TODO: Pydantic의 BaseSettings를 사용하여 Settings 클래스를 구현하세요
#   - 환경 변수에서 설정 값을 자동으로 로드합니다
#   - 필요한 설정 항목:
#     - APP_NAME: 앱 이름 (기본값: "ML Serving API")
#     - SECRET_KEY: JWT 서명용 비밀 키
#     - ALGORITHM: JWT 알고리즘 (기본값: "HS256")
#     - ACCESS_TOKEN_EXPIRE_MINUTES: 토큰 만료 시간 (기본값: 30)
#     - MODEL_PATH: ML 모델 파일 경로
#   - (참고: Phase 2 - 설정 관리, 환경 변수)


# TODO: Settings 인스턴스를 생성하는 함수를 구현하세요
#   - lru_cache 데코레이터를 사용하여 캐싱하는 것을 권장합니다
#   - (참고: Phase 2 - 의존성 주입)
