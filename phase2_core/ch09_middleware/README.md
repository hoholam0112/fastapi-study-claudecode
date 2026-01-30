# Chapter 09: 미들웨어 (Middleware)

## 학습 목표

- 미들웨어의 개념과 요청/응답 파이프라인의 동작 원리를 이해한다.
- CORS(Cross-Origin Resource Sharing)의 필요성과 설정 방법을 익힌다.
- 커스텀 미들웨어를 두 가지 방식(`@app.middleware` 데코레이터, `BaseHTTPMiddleware` 클래스)으로 작성할 수 있다.
- 미들웨어의 실행 순서를 이해하고, 실무에서 자주 사용하는 패턴을 적용할 수 있다.

---

## 핵심 개념

### 1. 미들웨어란?

미들웨어는 **모든 요청(Request)과 응답(Response) 사이에서 동작하는 코드**이다. 클라이언트의 요청이 엔드포인트에 도달하기 전, 그리고 응답이 클라이언트에게 반환되기 전에 실행된다.

```
클라이언트 요청
    │
    ▼
┌──────────────────────┐
│  미들웨어 A (진입)     │  ← 가장 나중에 등록된 미들웨어가 가장 먼저 실행
│  ┌──────────────────┐ │
│  │ 미들웨어 B (진입)  │ │
│  │  ┌──────────────┐ │ │
│  │  │ 미들웨어 C    │ │ │  ← 가장 먼저 등록된 미들웨어가 가장 나중에 실행
│  │  │  ┌────────┐  │ │ │
│  │  │  │엔드포인트│  │ │ │
│  │  │  └────────┘  │ │ │
│  │  │ 미들웨어 C    │ │ │
│  │  └──────────────┘ │ │
│  │ 미들웨어 B (반환)  │ │
│  └──────────────────┘ │
│  미들웨어 A (반환)     │
└──────────────────────┘
    │
    ▼
클라이언트 응답
```

### 2. CORS (Cross-Origin Resource Sharing)

CORS는 브라우저가 **다른 출처(origin)의 리소스에 접근하는 것을 제어**하는 보안 메커니즘이다.

| 설정 항목 | 설명 | 예시 |
|-----------|------|------|
| `allow_origins` | 허용할 출처 목록 | `["http://localhost:3000"]` |
| `allow_methods` | 허용할 HTTP 메서드 | `["GET", "POST", "PUT"]` |
| `allow_headers` | 허용할 요청 헤더 | `["Authorization", "Content-Type"]` |
| `allow_credentials` | 쿠키/인증 정보 허용 여부 | `True` / `False` |
| `expose_headers` | 브라우저에 노출할 응답 헤더 | `["X-Process-Time"]` |

> **주의**: `allow_origins=["*"]`와 `allow_credentials=True`는 동시에 사용할 수 없다. 자격 증명을 허용하려면 구체적인 출처를 명시해야 한다.

### 3. 커스텀 미들웨어 작성 방식

#### 방식 1: `@app.middleware("http")` 데코레이터

간단한 미들웨어에 적합하다. 함수 하나로 빠르게 작성할 수 있다.

```python
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    # 요청 전처리
    response = await call_next(request)
    # 응답 후처리
    return response
```

#### 방식 2: `BaseHTTPMiddleware` 클래스 상속

복잡한 로직이나 상태 관리가 필요한 경우에 적합하다. 재사용과 테스트가 용이하다.

```python
from starlette.middleware.base import BaseHTTPMiddleware

class MyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, some_param: str):
        super().__init__(app)
        self.some_param = some_param

    async def dispatch(self, request: Request, call_next):
        # 요청 전처리
        response = await call_next(request)
        # 응답 후처리
        return response
```

### 4. 미들웨어 실행 순서

FastAPI(Starlette)에서 미들웨어는 **등록 순서의 역순**으로 실행된다. 즉, 가장 나중에 `app.add_middleware()`로 등록한 미들웨어가 요청을 가장 먼저 처리한다.

```python
app.add_middleware(MiddlewareA)  # 세 번째로 요청 처리 (엔드포인트에 가장 가까움)
app.add_middleware(MiddlewareB)  # 두 번째로 요청 처리
app.add_middleware(MiddlewareC)  # 첫 번째로 요청 처리 (클라이언트에 가장 가까움)
```

실행 흐름: `C 진입 → B 진입 → A 진입 → 엔드포인트 → A 반환 → B 반환 → C 반환`

---

## 코드 실행 방법

### 1. 의존성 설치

```bash
pip install fastapi uvicorn
```

### 2. 서버 실행

```bash
cd /Users/zeroman0112/Projects/fastapi-study/phase2_core/ch09_middleware
uvicorn main:app --reload
```

### 3. API 테스트

```bash
# 기본 엔드포인트 호출 - 응답 헤더에 X-Process-Time, X-Request-ID 확인
curl -v http://localhost:8000/

# 아이템 목록 조회
curl http://localhost:8000/items

# 지연 응답 테스트 (처리 시간 측정 확인)
curl -v http://localhost:8000/slow

# 미들웨어 실행 순서 확인
curl http://localhost:8000/middleware-order

# Swagger UI에서 테스트
open http://localhost:8000/docs
```

### 4. CORS 테스트

브라우저 개발자 도구(Network 탭)에서 다른 출처의 요청을 보내거나, 아래 HTML을 로컬 파일로 열어서 테스트한다.

```html
<script>
fetch('http://localhost:8000/items')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
</script>
```

---

## 실습 포인트

1. **처리 시간 측정**: `curl -v http://localhost:8000/slow`를 호출하고 응답 헤더의 `X-Process-Time` 값을 확인해보자. 일반 엔드포인트와 비교하여 차이를 관찰한다.

2. **요청 ID 추적**: `X-Request-ID` 헤더가 매 요청마다 고유하게 생성되는지 확인한다. 서버 로그에서 해당 ID로 요청을 추적할 수 있다.

3. **미들웨어 실행 순서**: `/middleware-order` 엔드포인트를 호출하고 서버 콘솔 로그를 확인하여 미들웨어가 어떤 순서로 실행되는지 직접 관찰한다.

4. **CORS 동작 확인**: 브라우저에서 `http://localhost:3000` 등 다른 출처로부터의 요청이 허용/차단되는 것을 확인한다. `allow_origins` 설정을 변경해가며 테스트한다.

5. **데코레이터 방식 vs 클래스 방식**: 코드에서 두 가지 방식의 미들웨어를 비교하고, 각각의 장단점을 정리한다. 새로운 미들웨어를 직접 추가해본다.

6. **미들웨어 제거 실험**: 미들웨어를 하나씩 주석 처리해보며 동작 차이를 확인한다.
