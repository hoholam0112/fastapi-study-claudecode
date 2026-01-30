# Chapter 06: 의존성 주입 (Dependency Injection)

## 학습 목표

- 의존성 주입(DI)의 개념과 필요성을 이해한다
- FastAPI의 `Depends()` 시스템을 활용하여 코드 재사용성을 높인다
- 함수 기반 의존성과 클래스 기반 의존성의 차이를 파악한다
- `yield`를 사용하여 리소스의 생성과 정리를 안전하게 관리한다
- 의존성 체이닝을 통해 인증/인가 파이프라인을 구축한다

## 핵심 개념

### 1. 의존성 주입(DI)이란?

의존성 주입은 컴포넌트가 필요로 하는 의존성을 외부에서 제공(주입)하는 디자인 패턴이다.
FastAPI는 `Depends()`를 통해 이 패턴을 프레임워크 레벨에서 지원한다.

**DI의 장점:**
- 코드 재사용성 향상
- 테스트 용이성 (Mock 주입 가능)
- 관심사의 분리 (Separation of Concerns)
- 코드 중복 제거

### 2. 함수 기반 의존성

가장 기본적인 의존성 형태로, 일반 함수를 `Depends()`에 전달한다.

```python
def common_parameters(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons
```

### 3. 클래스 기반 의존성

클래스를 의존성으로 사용하면 상태를 가진 의존성을 만들 수 있다.
`__init__` 메서드의 매개변수가 자동으로 요청 파라미터와 매핑된다.

```python
class CommonQueryParams:
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit
```

### 4. yield 의존성 (리소스 관리)

`yield`를 사용하면 요청 처리 전후로 리소스를 관리할 수 있다.
데이터베이스 세션, 파일 핸들, 네트워크 연결 등의 관리에 적합하다.

```python
async def get_db():
    db = SessionLocal()  # 리소스 생성
    try:
        yield db           # 리소스 제공
    finally:
        db.close()         # 리소스 정리 (반드시 실행)
```

### 5. 의존성 체이닝

의존성이 다른 의존성에 의존하는 구조를 만들 수 있다.
인증/인가 파이프라인 구축에 자주 사용된다.

```
verify_token -> get_current_user -> get_active_user
```

## 코드 실행 방법

```bash
# 챕터 디렉토리로 이동
cd phase2_core/ch06_dependency_injection

# 서버 실행
uvicorn main:app --reload

# API 문서 확인
# http://127.0.0.1:8000/docs
```

### 주요 엔드포인트 테스트

```bash
# 함수 기반 의존성 테스트
curl "http://127.0.0.1:8000/items/?skip=0&limit=10"

# 클래스 기반 의존성 테스트
curl "http://127.0.0.1:8000/items-class/?skip=5&limit=20"

# yield 의존성 (DB 세션 시뮬레이션) 테스트
curl "http://127.0.0.1:8000/db-items/"

# 의존성 체이닝 (인증 필요) 테스트
curl -H "X-Token: fake-secret-token" "http://127.0.0.1:8000/users/me"

# 라우터 레벨 의존성 테스트
curl -H "X-Token: fake-secret-token" "http://127.0.0.1:8000/admin/dashboard"
```

## 실습 포인트

1. **함수 의존성 직접 만들기**: 페이지네이션 파라미터를 처리하는 의존성 함수를 작성해 보자
2. **클래스 의존성 확장**: `CommonQueryParams`에 정렬(sort) 파라미터를 추가해 보자
3. **yield 의존성 실험**: 의도적으로 예외를 발생시켜 `finally` 블록이 실행되는지 확인해 보자
4. **체이닝 확장**: 역할(role) 기반 접근 제어 의존성을 추가해 보자
5. **테스트 작성**: `app.dependency_overrides`를 사용하여 의존성을 Mock으로 교체하는 테스트를 작성해 보자

## 참고 자료

- [FastAPI 공식 문서 - Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI 공식 문서 - Classes as Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/)
- [FastAPI 공식 문서 - Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
