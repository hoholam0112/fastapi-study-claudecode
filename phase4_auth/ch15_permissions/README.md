# Chapter 15: 권한 관리 (Permissions)

## 학습 목표

- **Role 기반 접근 제어 (RBAC)** 패턴을 이해하고 FastAPI에서 구현할 수 있다.
- **OAuth2 Scopes**를 활용하여 세분화된 권한 제어를 적용할 수 있다.
- **API Key 인증** 방식을 구현하여 서비스 간 통신을 보호할 수 있다.
- **권한 데코레이터 패턴**을 활용하여 재사용 가능한 인증/인가 로직을 설계할 수 있다.

---

## 핵심 개념

### 1. Role 기반 접근 제어 (RBAC)

RBAC는 사용자에게 역할(Role)을 부여하고, 각 역할에 따라 접근 가능한 리소스를 제한하는 방식이다.

| 역할 | 설명 | 접근 가능 범위 |
|------|------|---------------|
| `admin` | 관리자 | 모든 엔드포인트 접근 가능 |
| `user` | 일반 사용자 | 읽기/쓰기 엔드포인트 접근 가능 |
| `viewer` | 조회 전용 사용자 | 읽기 전용 엔드포인트만 접근 가능 |

```python
class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
```

### 2. OAuth2 Scopes

OAuth2 Scopes는 토큰에 부여된 권한의 범위를 정의한다. 각 엔드포인트에 필요한 scope를 지정하여 세밀한 접근 제어가 가능하다.

- `items:read` - 아이템 조회 권한
- `items:write` - 아이템 생성/수정 권한
- `admin` - 관리자 전용 기능 권한

### 3. API Key 인증

서비스 간 통신이나 외부 클라이언트 인증에 사용되는 간단한 인증 방식이다. HTTP 헤더의 `X-API-Key` 값을 검증하여 요청의 유효성을 확인한다.

### 4. 권한 데코레이터 패턴

FastAPI의 `Depends()`를 활용하여 권한 검증 로직을 재사용 가능한 의존성으로 분리하는 패턴이다.

```python
# 특정 역할만 허용하는 의존성 생성
def role_required(allowed_roles: list[Role]):
    def checker(user = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403)
        return user
    return checker
```

---

## 코드 실행 방법

### 사전 준비

```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt]
```

### 서버 실행

```bash
cd phase4_auth/ch15_permissions
uvicorn main:app --reload
```

### API 문서 확인

서버 실행 후 브라우저에서 접속:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 테스트 계정

| 사용자명 | 비밀번호 | 역할 | Scopes |
|---------|---------|------|--------|
| `admin` | `admin1234` | admin | items:read, items:write, admin |
| `user1` | `user1234` | user | items:read, items:write |
| `viewer1` | `viewer1234` | viewer | items:read |

### API 테스트 예시

```bash
# 1. 토큰 발급 (admin)
curl -X POST http://127.0.0.1:8000/token \
  -d "username=admin&password=admin1234&scope=items:read items:write admin"

# 2. 토큰으로 보호된 엔드포인트 호출
curl http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer <발급받은_토큰>"

# 3. API Key 인증
curl http://127.0.0.1:8000/apikey/data \
  -H "X-API-Key: supersecretapikey123"
```

---

## 실습 포인트

1. **역할별 접근 테스트**: `admin`, `user`, `viewer` 각각의 계정으로 로그인한 후, 권한이 없는 엔드포인트에 접근하면 어떤 응답이 반환되는지 확인한다.

2. **Scope 제한 테스트**: 토큰 발급 시 요청하는 scope를 변경하여, 부여되지 않은 scope의 엔드포인트에 접근했을 때의 동작을 확인한다.

3. **API Key 인증 테스트**: 올바른 키와 잘못된 키를 각각 전송하여 인증 로직이 정상 동작하는지 확인한다.

4. **권한 조합 설계**: 새로운 역할(예: `editor`)을 추가하고, 해당 역할에 맞는 scope와 엔드포인트를 설계해 본다.

5. **에러 응답 분석**: `401 Unauthorized`와 `403 Forbidden`의 차이를 이해하고, 각각 어떤 상황에서 반환되는지 정리한다.
