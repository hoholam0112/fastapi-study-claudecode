# Chapter 04 - 응답 모델과 응답 타입

## 학습 목표

- `response_model`을 사용하여 API 응답의 형태를 명시적으로 정의할 수 있다
- HTTP 상태 코드를 상황에 맞게 설정할 수 있다 (201 Created, 204 No Content 등)
- `response_model_exclude`, `response_model_include` 옵션으로 응답 필드를 제어할 수 있다
- `JSONResponse`, `HTMLResponse`, `RedirectResponse` 등 다양한 응답 타입을 활용할 수 있다
- 하나의 엔드포인트에서 여러 응답 모델을 문서화할 수 있다

## 핵심 개념

### 1. response_model

`response_model`은 엔드포인트가 반환하는 데이터의 스키마를 정의한다. FastAPI는 이 모델을 기반으로:

- 반환 데이터를 자동으로 직렬화(serialize)한다
- OpenAPI 문서(Swagger UI)에 응답 스키마를 표시한다
- 모델에 정의되지 않은 필드를 자동으로 필터링한다

```python
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    return user  # UserResponse 스키마에 맞게 자동 변환
```

### 2. status_code 설정

HTTP 상태 코드는 API 응답의 의미를 클라이언트에게 전달한다:

| 상태 코드 | 의미 | 사용 예시 |
|-----------|------|----------|
| 200 | OK (기본값) | 조회 성공 |
| 201 | Created | 리소스 생성 성공 |
| 204 | No Content | 삭제 성공 (본문 없음) |
| 404 | Not Found | 리소스를 찾을 수 없음 |
| 422 | Unprocessable Entity | 유효성 검사 실패 |

```python
@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    ...
```

### 3. response_model_exclude / response_model_include

민감한 정보(비밀번호 등)를 응답에서 제외하거나, 특정 필드만 포함할 수 있다:

```python
# password 필드를 응답에서 제외
@app.get("/users/{id}", response_model=User, response_model_exclude={"password"})

# name과 email 필드만 응답에 포함
@app.get("/users/{id}", response_model=User, response_model_include={"name", "email"})
```

> 실무에서는 `response_model_exclude` 대신 별도의 응답 전용 Pydantic 모델을 만드는 것이 더 권장된다.

### 4. 다양한 응답 타입

FastAPI는 JSON 외에도 다양한 형식으로 응답할 수 있다:

- **JSONResponse**: 커스텀 헤더나 상태 코드를 포함한 JSON 응답
- **HTMLResponse**: HTML 문자열을 반환
- **RedirectResponse**: 다른 URL로 리다이렉트
- **PlainTextResponse**: 일반 텍스트 응답

### 5. 다중 응답 모델 (responses 파라미터)

하나의 엔드포인트에서 상태 코드별로 다른 응답 모델을 문서화할 수 있다:

```python
@app.get("/items/{id}", responses={
    200: {"model": ItemResponse},
    404: {"model": ErrorResponse},
})
```

## 코드 실행 방법

```bash
# ch04_response 디렉토리로 이동
cd phase1_basics/ch04_response

# 서버 실행
uvicorn main:app --reload

# 브라우저에서 API 문서 확인
# http://127.0.0.1:8000/docs
```

## 실습 포인트

1. **response_model 효과 확인**: `/users/` POST 요청 후, 응답에 `password` 필드가 포함되지 않는 것을 확인한다
2. **상태 코드 확인**: Swagger UI 또는 curl로 요청하여 201, 204 등 상태 코드가 올바르게 반환되는지 확인한다
3. **다양한 응답 타입 테스트**: `/html`, `/redirect`, `/custom-header` 엔드포인트를 각각 호출하여 응답 형태를 비교한다
4. **response_model_exclude 실험**: exclude 옵션을 변경하여 어떤 필드가 제외되는지 확인한다
5. **OpenAPI 문서 비교**: `/docs`에서 각 엔드포인트의 응답 스키마가 어떻게 표시되는지 비교한다

### 추가 도전 과제

- `response_model_exclude_unset=True` 옵션을 적용하여 설정되지 않은 기본값 필드를 제외해 보자
- 파일 다운로드를 위한 `FileResponse`를 추가해 보자
- `responses` 파라미터를 활용하여 에러 응답까지 Swagger에 문서화해 보자
