# Chapter 18: FastAPI 테스트

## 학습 목표

- FastAPI 애플리케이션의 테스트 방법을 이해한다
- `TestClient`를 사용하여 API 엔드포인트를 테스트할 수 있다
- `pytest`의 기본 사용법과 fixture를 익힌다
- 의존성 오버라이드(dependency override)를 활용한 테스트 격리 기법을 학습한다
- 비동기 테스트의 개념과 필요성을 이해한다

## 핵심 개념

### 1. TestClient

FastAPI는 Starlette의 `TestClient`를 제공하며, 이를 통해 실제 서버를 실행하지 않고도 API를 테스트할 수 있다. 내부적으로 `httpx`를 사용하여 HTTP 요청을 시뮬레이션한다.

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.get("/items/")
assert response.status_code == 200
```

### 2. pytest 기본

`pytest`는 Python의 대표적인 테스트 프레임워크이다.

- **테스트 함수**: `test_`로 시작하는 함수를 자동으로 테스트로 인식한다
- **fixture**: 테스트에 필요한 사전 설정을 재사용 가능하게 정의한다
- **assert**: Python 내장 `assert`문을 사용하여 검증한다

```python
import pytest

@pytest.fixture
def client():
    return TestClient(app)

def test_example(client):
    response = client.get("/")
    assert response.status_code == 200
```

### 3. 의존성 오버라이드 (Dependency Override)

테스트 환경에서는 실제 데이터베이스 대신 테스트용 데이터를 사용해야 한다. FastAPI의 `dependency_overrides`를 사용하면 특정 의존성을 테스트용으로 교체할 수 있다.

```python
def override_get_db():
    return {"test_item": {"name": "테스트 아이템", "price": 1000}}

app.dependency_overrides[get_db] = override_get_db
```

### 4. 비동기 테스트

`async def`로 정의된 엔드포인트를 직접 테스트하려면 `httpx.AsyncClient`와 `pytest-asyncio`를 사용한다. 일반적인 `TestClient`는 동기적으로 동작하므로 대부분의 경우 충분하지만, 비동기 의존성이나 이벤트 루프가 필요한 경우 비동기 테스트가 필요하다.

```python
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_async_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/items/")
    assert response.status_code == 200
```

## 코드 실행 방법

### 사전 준비

```bash
pip install fastapi uvicorn pytest httpx
```

### 앱 실행 (테스트 대상 확인용)

```bash
uvicorn main:app --reload
```

### 테스트 실행

```bash
# 기본 실행
pytest test_main.py

# 상세 출력 모드
pytest test_main.py -v

# 특정 테스트만 실행
pytest test_main.py::test_create_item -v

# 실패한 테스트만 재실행
pytest test_main.py --lf
```

## 실습 포인트

1. **기본 CRUD 테스트**: 각 엔드포인트(POST, GET, DELETE)에 대한 테스트를 작성하고 실행해 본다
2. **에러 케이스 테스트**: 존재하지 않는 리소스 접근 시 404 응답을 확인한다
3. **의존성 오버라이드**: `get_db` 의존성을 테스트용으로 교체하여 격리된 테스트를 수행한다
4. **fixture 활용**: `@pytest.fixture`로 공통 설정을 분리하여 테스트 코드의 중복을 줄인다
5. **테스트 순서 독립성**: 각 테스트가 서로 영향을 주지 않도록 설계한다

## 참고 자료

- [FastAPI 공식 문서 - Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest 공식 문서](https://docs.pytest.org/)
- [httpx 공식 문서](https://www.python-httpx.org/)
