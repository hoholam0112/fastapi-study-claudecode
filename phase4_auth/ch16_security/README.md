# Chapter 16: 보안 강화 (Security Hardening)

## 학습 목표

- **환경변수 관리**: `pydantic-settings`를 사용하여 설정을 안전하게 관리할 수 있다.
- **Rate Limiting**: 요청 속도 제한을 구현하여 서비스 남용을 방지할 수 있다.
- **보안 헤더**: 미들웨어를 통해 주요 보안 헤더를 응답에 자동 추가할 수 있다.
- **CORS 설정**: 허용된 출처만 API에 접근할 수 있도록 CORS를 구성할 수 있다.
- **HTTPS 관련 개념**: 프로덕션 환경에서의 HTTPS 설정 방법을 이해할 수 있다.

---

## 핵심 개념

### 1. 환경변수 관리 (pydantic-settings)

민감한 설정 값(비밀 키, 데이터베이스 URL 등)을 코드에 직접 작성하면 보안 위험이 발생한다. `pydantic-settings`를 사용하면 `.env` 파일이나 환경변수에서 설정을 안전하게 로드할 수 있다.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env")
```

**주요 특징:**
- 타입 검증: 설정 값의 타입을 자동으로 검증
- 기본값 지원: 환경변수가 없을 때 기본값 사용
- `.env` 파일 지원: 개발 환경에서 편리하게 설정 관리
- `lru_cache`: 설정 인스턴스를 캐싱하여 성능 최적화

### 2. Rate Limiting (요청 속도 제한)

API 남용을 방지하기 위해 특정 시간 내 요청 횟수를 제한하는 기법이다.

| 방식 | 설명 | 장점 | 단점 |
|------|------|------|------|
| In-Memory | 서버 메모리에 요청 기록 저장 | 구현 간단 | 서버 재시작 시 초기화, 다중 서버 불가 |
| Redis 기반 | Redis에 요청 기록 저장 | 다중 서버 지원, 영속성 | 별도 인프라 필요 |
| Token Bucket | 토큰 버킷 알고리즘 | 버스트 트래픽 허용 | 구현 복잡 |

본 예제에서는 학습 목적으로 In-Memory 방식을 구현한다.

### 3. 보안 헤더

HTTP 응답에 보안 관련 헤더를 추가하여 다양한 공격을 방어한다.

| 헤더 | 값 | 방어 대상 |
|------|---|----------|
| `X-Content-Type-Options` | `nosniff` | MIME 타입 스니핑 공격 |
| `X-Frame-Options` | `DENY` | 클릭재킹 (Clickjacking) |
| `X-XSS-Protection` | `1; mode=block` | 반사형 XSS 공격 |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | 프로토콜 다운그레이드 |
| `Content-Security-Policy` | `default-src 'self'` | XSS 및 데이터 주입 |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | 리퍼러 정보 유출 |
| `Permissions-Policy` | `camera=(), microphone=()` | 브라우저 기능 악용 |

### 4. CORS (Cross-Origin Resource Sharing)

브라우저의 Same-Origin Policy를 확장하여, 허용된 출처에서만 API에 접근할 수 있도록 제어한다.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],  # 허용할 출처
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**주의사항:**
- `allow_origins=["*"]`는 개발 환경에서만 사용해야 한다.
- 프로덕션에서는 반드시 허용할 도메인을 명시적으로 지정한다.

### 5. HTTPS 설정

프로덕션 환경에서는 반드시 HTTPS를 사용해야 한다.

```bash
# uvicorn으로 직접 HTTPS 실행 (개발/테스트용)
uvicorn main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem

# 프로덕션에서는 Nginx 등 리버스 프록시 뒤에서 실행하는 것을 권장
```

---

## 코드 실행 방법

### 사전 준비

```bash
pip install fastapi uvicorn pydantic-settings
```

### 환경변수 파일 생성 (선택사항)

`.env` 파일을 `ch16_security/` 디렉토리에 생성하면 설정을 커스터마이징할 수 있다.

```dotenv
APP_NAME=FastAPI 보안 예제
DEBUG=true
SECRET_KEY=your-super-secret-key-change-in-production
DATABASE_URL=sqlite:///./test.db
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080"]
API_KEY=my-custom-api-key
```

> `.env` 파일이 없어도 기본값으로 정상 실행된다.

### 서버 실행

```bash
cd phase4_auth/ch16_security
uvicorn main:app --reload
```

### API 문서 확인

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 테스트 예시

```bash
# 1. 공개 엔드포인트 접근
curl http://127.0.0.1:8000/

# 2. Rate Limiting 테스트 (빠르게 반복 요청)
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/limited
done

# 3. 보안 헤더 확인
curl -I http://127.0.0.1:8000/

# 4. 설정 정보 확인 (민감 정보는 마스킹)
curl http://127.0.0.1:8000/settings/info

# 5. 보호된 엔드포인트 (API Key)
curl http://127.0.0.1:8000/protected/data \
  -H "X-API-Key: changeme-secret-api-key"
```

---

## 실습 포인트

1. **Rate Limiting 동작 확인**: `/limited` 엔드포인트에 빠르게 반복 요청을 보내서 429 응답을 확인한다. 제한 시간이 지난 후 다시 요청하여 정상 응답이 되는지도 확인한다.

2. **보안 헤더 검증**: `curl -I` 명령으로 응답 헤더를 확인하고, 각 보안 헤더의 역할을 정리한다.

3. **환경변수 우선순위**: `.env` 파일과 시스템 환경변수에 같은 키를 다른 값으로 설정한 후, 어느 쪽이 우선하는지 확인한다.

4. **CORS 테스트**: 브라우저의 개발자 도구(Console)에서 `fetch()` API로 다른 출처에서의 요청을 시도하여 CORS 동작을 확인한다.

5. **설정 확장**: `config.py`에 새로운 설정 값(예: `RATE_LIMIT_PER_MINUTE`, `LOG_LEVEL`)을 추가하고, `main.py`에서 해당 설정을 활용하도록 수정해 본다.

6. **프로덕션 체크리스트 작성**: 실제 서비스 배포 시 필요한 보안 설정 항목을 정리해 본다.
