# Chapter 14: JWT 인증 (JSON Web Token Authentication)

## 학습 목표

- OAuth2의 개념과 Password Flow 인증 방식을 이해한다.
- JWT(JSON Web Token)의 구조와 동작 원리를 파악한다.
- bcrypt를 활용한 비밀번호 해싱 및 검증 방법을 익힌다.
- FastAPI에서 `OAuth2PasswordBearer`를 사용하여 토큰 기반 인증을 구현한다.
- 보호된 엔드포인트에 의존성 주입(`Depends`)으로 인증을 적용한다.

---

## 핵심 개념

### 1. OAuth2와 Password Flow

OAuth2는 인증 및 권한 부여를 위한 업계 표준 프로토콜이다.
다양한 Flow(흐름) 중 **Password Flow**는 사용자가 직접 아이디와 비밀번호를 입력하여 토큰을 발급받는 방식이다.

```
[사용자] --(username + password)--> [서버]
[서버]   --(access_token)---------> [사용자]
[사용자] --(Authorization: Bearer token)--> [보호된 API]
```

> Password Flow는 자사 서비스(First-party) 클라이언트에서 주로 사용한다.
> 외부 서비스 연동 시에는 Authorization Code Flow를 권장한다.

### 2. JWT 토큰 구조

JWT는 세 부분으로 구성되며, 각각 Base64URL로 인코딩되어 `.`으로 연결된다.

```
header.payload.signature
```

| 구성 요소 | 설명 | 예시 |
|-----------|------|------|
| **Header** | 토큰 타입과 서명 알고리즘 | `{"alg": "HS256", "typ": "JWT"}` |
| **Payload** | 사용자 정보 및 클레임(Claims) | `{"sub": "username", "exp": 1234567890}` |
| **Signature** | 위변조 방지를 위한 서명 | `HMACSHA256(base64(header) + "." + base64(payload), secret)` |

주요 클레임(Claims):
- `sub` (Subject): 토큰의 주체 (보통 사용자 식별자)
- `exp` (Expiration): 토큰 만료 시간 (Unix timestamp)
- `iat` (Issued At): 토큰 발급 시간

### 3. 비밀번호 해싱 (bcrypt)

비밀번호를 평문으로 저장하면 데이터 유출 시 치명적이다.
**bcrypt**는 단방향 해시 함수로, 다음과 같은 특징이 있다:

- **단방향성**: 해시값에서 원본 비밀번호를 복원할 수 없다.
- **솔트(Salt)**: 같은 비밀번호도 매번 다른 해시값을 생성한다.
- **적응형 비용(Cost Factor)**: 연산 비용을 조절하여 무차별 대입 공격에 대응한다.

```python
# 해싱 예시
plain_password = "mypassword123"
hashed = "$2b$12$EixZaYVK1fsbw1ZfbX3OXe..."  # bcrypt 해시 결과
```

### 4. FastAPI의 OAuth2PasswordBearer

FastAPI는 `OAuth2PasswordBearer`를 통해 OAuth2 Password Flow를 간편하게 구현할 수 있다.

```python
from fastapi.security import OAuth2PasswordBearer

# tokenUrl: 토큰 발급 엔드포인트 경로
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

- 요청 헤더에서 `Authorization: Bearer <token>` 형식의 토큰을 자동으로 추출한다.
- Swagger UI에서 자물쇠 아이콘을 클릭하여 인증 테스트가 가능하다.

---

## 프로젝트 구조

```
ch14_jwt_auth/
├── README.md       # 학습 가이드 (현재 파일)
├── schemas.py      # Pydantic 모델 (요청/응답 스키마)
├── auth.py         # 인증 로직 (JWT 생성/검증, 비밀번호 해싱)
└── main.py         # FastAPI 애플리케이션 (엔드포인트 정의)
```

---

## 코드 실행 방법

### 1. 필수 패키지 설치

```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] python-multipart
```

| 패키지 | 용도 |
|--------|------|
| `fastapi` | 웹 프레임워크 |
| `uvicorn` | ASGI 서버 |
| `python-jose[cryptography]` | JWT 토큰 생성 및 검증 |
| `passlib[bcrypt]` | 비밀번호 해싱 (bcrypt) |
| `python-multipart` | OAuth2PasswordRequestForm 파싱에 필요 |

### 2. 서버 실행

```bash
cd phase4_auth/ch14_jwt_auth
uvicorn main:app --reload
```

### 3. API 문서 확인

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## 테스트 순서

아래 순서대로 API를 호출하여 전체 인증 흐름을 테스트한다.

### Step 1: 회원가입

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

**기대 응답:**
```json
{
  "message": "회원가입이 완료되었습니다.",
  "username": "testuser"
}
```

### Step 2: 로그인 (토큰 발급)

```bash
curl -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

**기대 응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

```

> `Content-Type`이 `application/x-www-form-urlencoded`인 것에 주의한다.
> OAuth2 Password Flow 사양에 따른 것이다.

### Step 3: 토큰으로 보호된 API 접근

```bash
# 위에서 받은 access_token 값을 사용한다.
curl -X GET http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer <여기에_토큰_붙여넣기>"
```

**기대 응답:**
```json
{
  "username": "testuser",
  "email": null,
  "disabled": false
}
```

### Step 4: 보호된 엔드포인트 접근

```bash
curl -X GET http://127.0.0.1:8000/protected \
  -H "Authorization: Bearer <여기에_토큰_붙여넣기>"
```

**기대 응답:**
```json
{
  "message": "이 엔드포인트는 인증된 사용자만 접근할 수 있습니다.",
  "user": "testuser"
}
```

### 토큰 없이 접근 시

```bash
curl -X GET http://127.0.0.1:8000/users/me
```

**기대 응답 (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

---

## 실습 포인트

### 기본 실습
1. Swagger UI(`/docs`)에서 자물쇠 아이콘을 클릭하여 로그인 후 보호된 API를 호출해 본다.
2. 발급받은 JWT 토큰을 [jwt.io](https://jwt.io)에 붙여넣어 디코딩된 내용을 확인한다.
3. 잘못된 비밀번호로 로그인을 시도하여 에러 응답을 확인한다.
4. 토큰 만료 시간(`ACCESS_TOKEN_EXPIRE_MINUTES`)을 1분으로 줄여 만료 동작을 관찰한다.

### 심화 실습
5. 이미 존재하는 사용자명으로 회원가입을 시도하여 중복 검사가 동작하는지 확인한다.
6. `auth.py`의 `SECRET_KEY`를 변경한 뒤 기존 토큰이 무효화되는지 테스트한다.
7. 사용자 비활성화(`disabled=True`) 기능을 추가하여 비활성 사용자의 접근을 차단해 본다.
8. Refresh Token 메커니즘을 직접 설계하고 구현해 본다.

---

## 참고 자료

- [FastAPI 공식 문서 - Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT 공식 사이트](https://jwt.io/)
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [OWASP 비밀번호 저장 가이드라인](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
