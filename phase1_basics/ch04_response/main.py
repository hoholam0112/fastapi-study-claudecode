"""
Chapter 04 - 응답 모델과 응답 타입
=================================
이 모듈에서는 FastAPI의 응답 처리 방법을 학습한다:
- response_model을 활용한 응답 스키마 정의
- HTTP 상태 코드 설정
- response_model_exclude로 민감 정보 제외
- JSONResponse, HTMLResponse, RedirectResponse 등 다양한 응답 타입
- 다중 응답 모델(responses 파라미터) 문서화

실행 방법:
    uvicorn main:app --reload
"""

from fastapi import FastAPI, status, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, PlainTextResponse
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

app = FastAPI(
    title="Chapter 04 - 응답 모델과 응답 타입",
    description="response_model, status_code, 다양한 응답 타입을 학습하는 API",
    version="1.0.0",
)

# ============================================================
# Pydantic 모델 정의
# ============================================================

# --- 사용자(User) 관련 모델 ---


class UserCreate(BaseModel):
    """사용자 생성 요청 모델 (클라이언트 -> 서버)"""
    username: str = Field(..., min_length=2, max_length=30, examples=["홍길동"])
    email: str = Field(..., examples=["hong@example.com"])
    password: str = Field(..., min_length=8, examples=["securepass123"])
    bio: str | None = Field(default=None, examples=["안녕하세요, 개발자입니다."])


class UserResponse(BaseModel):
    """
    사용자 응답 모델 (서버 -> 클라이언트)
    password 필드가 없다 - 응답에 민감 정보를 포함하지 않기 위함이다.
    실무에서는 이처럼 요청/응답 모델을 분리하는 것이 권장된다.
    """
    id: int
    username: str
    email: str
    bio: str | None = None
    created_at: datetime


class UserInDB(BaseModel):
    """
    내부 저장용 모델 (DB에 저장되는 전체 데이터)
    password를 포함하며, 서버 내부에서만 사용한다.
    """
    id: int
    username: str
    email: str
    password: str
    bio: str | None = None
    created_at: datetime


# --- 상품(Item) 관련 모델 ---


class ItemCreate(BaseModel):
    """상품 생성 요청 모델"""
    name: str = Field(..., examples=["무선 키보드"])
    description: str | None = Field(default=None, examples=["블루투스 기계식 키보드"])
    price: float = Field(..., gt=0, examples=[59000])
    tax: float | None = Field(default=None, ge=0, examples=[5900])


class ItemResponse(BaseModel):
    """상품 응답 모델 - 세금 포함 가격을 자동 계산하여 반환한다"""
    id: int
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    price_with_tax: float | None = None


# --- 에러 응답 모델 ---


class ErrorResponse(BaseModel):
    """에러 발생 시 반환하는 통일된 에러 응답 모델"""
    detail: str
    error_code: str | None = None


# ============================================================
# 인메모리 저장소 (실제 DB 대신 딕셔너리 사용)
# ============================================================

# 사용자 저장소
users_db: dict[int, UserInDB] = {}
user_id_counter: int = 0

# 상품 저장소
items_db: dict[int, dict] = {}
item_id_counter: int = 0


# ============================================================
# 1. response_model 기본 사용법
# ============================================================


@app.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새 사용자 생성",
    tags=["사용자"],
)
def create_user(user: UserCreate):
    """
    사용자를 생성한다.

    - **response_model=UserResponse**: 응답에서 password가 자동으로 제외된다.
      UserCreate에는 password가 있지만, UserResponse에는 없으므로
      FastAPI가 직렬화 시 password를 필터링한다.
    - **status_code=201**: 리소스 생성 성공을 나타내는 HTTP 상태 코드를 반환한다.
    """
    global user_id_counter
    user_id_counter += 1

    # 내부 저장용 모델에는 password를 포함하여 저장한다
    user_in_db = UserInDB(
        id=user_id_counter,
        username=user.username,
        email=user.email,
        password=user.password,  # 실제로는 해싱 후 저장해야 한다
        bio=user.bio,
        created_at=datetime.now(),
    )
    users_db[user_id_counter] = user_in_db

    # UserInDB 객체를 반환하지만, response_model=UserResponse 덕분에
    # password 필드는 응답에 포함되지 않는다
    return user_in_db


@app.get(
    "/users/",
    response_model=list[UserResponse],
    summary="전체 사용자 목록 조회",
    tags=["사용자"],
)
def list_users():
    """
    모든 사용자를 조회한다.

    - **response_model=list[UserResponse]**: 리스트 형태의 응답 모델도 지정 가능하다.
    - 각 사용자의 password는 응답에 포함되지 않는다.
    """
    return list(users_db.values())


# ============================================================
# 2. response_model_exclude 사용법
# ============================================================


@app.get(
    "/users/{user_id}/full",
    response_model=UserInDB,
    response_model_exclude={"password"},
    summary="사용자 상세 조회 (exclude 방식)",
    tags=["사용자"],
)
def get_user_with_exclude(user_id: int):
    """
    response_model_exclude를 사용하여 특정 필드를 응답에서 제외한다.

    이 방식은 간단하지만, 별도의 응답 모델(UserResponse)을 만드는 것이
    유지보수와 타입 안전성 측면에서 더 권장된다.

    - **response_model=UserInDB**: 내부 모델을 그대로 사용하되
    - **response_model_exclude={"password"}**: password 필드만 제외한다
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"사용자 ID {user_id}를 찾을 수 없습니다",
        )
    return users_db[user_id]


# ============================================================
# 3. response_model_include 사용법
# ============================================================


@app.get(
    "/users/{user_id}/summary",
    response_model=UserInDB,
    response_model_include={"id", "username", "email"},
    summary="사용자 요약 조회 (include 방식)",
    tags=["사용자"],
)
def get_user_summary(user_id: int):
    """
    response_model_include를 사용하여 특정 필드만 응답에 포함한다.

    - **response_model_include={"id", "username", "email"}**: 지정한 3개 필드만 반환된다.
    - bio, password, created_at 등 나머지 필드는 모두 제외된다.
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"사용자 ID {user_id}를 찾을 수 없습니다",
        )
    return users_db[user_id]


# ============================================================
# 4. 다양한 상태 코드 설정
# ============================================================


@app.post(
    "/items/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="상품 생성 (201 Created)",
    tags=["상품"],
)
def create_item(item: ItemCreate):
    """
    상품을 생성하고 201 Created 상태 코드를 반환한다.

    - **status_code=201**: POST로 리소스를 생성했을 때의 표준 상태 코드이다.
    - 세금(tax)이 있는 경우, 세금 포함 가격을 자동 계산한다.
    """
    global item_id_counter
    item_id_counter += 1

    # 세금 포함 가격 계산
    price_with_tax = item.price + item.tax if item.tax else item.price

    item_data = {
        "id": item_id_counter,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "tax": item.tax,
        "price_with_tax": price_with_tax,
    }
    items_db[item_id_counter] = item_data
    return item_data


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="상품 삭제 (204 No Content)",
    tags=["상품"],
)
def delete_item(item_id: int):
    """
    상품을 삭제하고 204 No Content 상태 코드를 반환한다.

    - **status_code=204**: 삭제 성공 시 본문(body) 없이 상태 코드만 반환한다.
    - 클라이언트는 상태 코드만으로 삭제 성공 여부를 판단할 수 있다.
    """
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"상품 ID {item_id}를 찾을 수 없습니다",
        )
    del items_db[item_id]
    # 204 응답은 본문이 없으므로 아무것도 반환하지 않는다
    return None


# ============================================================
# 5. 다중 응답 모델 (responses 파라미터)
# ============================================================


@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    responses={
        200: {
            "description": "상품 조회 성공",
            "model": ItemResponse,
        },
        404: {
            "description": "상품을 찾을 수 없음",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "상품 ID 999를 찾을 수 없습니다",
                        "error_code": "ITEM_NOT_FOUND",
                    }
                }
            },
        },
    },
    summary="상품 단건 조회 (다중 응답 모델)",
    tags=["상품"],
)
def get_item(item_id: int):
    """
    상품을 조회한다. 성공/실패에 따라 다른 응답 모델을 반환한다.

    - **responses 파라미터**: Swagger UI에 200과 404 응답을 모두 문서화한다.
    - 실제 404 발생 시 ErrorResponse 형태의 JSON을 반환한다.
    """
    if item_id not in items_db:
        # JSONResponse를 직접 반환하여 ErrorResponse 형태에 맞춘다
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": f"상품 ID {item_id}를 찾을 수 없습니다",
                "error_code": "ITEM_NOT_FOUND",
            },
        )
    return items_db[item_id]


# ============================================================
# 6. JSONResponse - 커스텀 헤더 포함 응답
# ============================================================


@app.get(
    "/custom-header",
    summary="커스텀 헤더가 포함된 JSON 응답",
    tags=["응답 타입"],
)
def get_with_custom_header():
    """
    JSONResponse를 직접 생성하여 커스텀 헤더를 포함한다.

    - **JSONResponse**: 응답 본문, 상태 코드, 헤더를 모두 직접 제어할 수 있다.
    - 캐시 제어, CORS, 커스텀 메타데이터 등을 헤더에 추가할 때 유용하다.
    """
    content = {
        "message": "커스텀 헤더가 포함된 응답입니다",
        "data": {"key": "value"},
    }
    headers = {
        "X-Custom-Header": "FastAPI-Study",
        "X-Request-Time": datetime.now().isoformat(),
        "Cache-Control": "no-cache",
    }
    return JSONResponse(
        content=content,
        status_code=status.HTTP_200_OK,
        headers=headers,
    )


# ============================================================
# 7. HTMLResponse - HTML 응답
# ============================================================


@app.get(
    "/html",
    response_class=HTMLResponse,
    summary="HTML 형식 응답",
    tags=["응답 타입"],
)
def get_html_response():
    """
    HTMLResponse를 사용하여 HTML 문서를 반환한다.

    - **response_class=HTMLResponse**: Swagger UI에서 응답 타입이 text/html로 표시된다.
    - 간단한 HTML 페이지나 위젯을 반환할 때 사용한다.
    - 본격적인 HTML 렌더링에는 Jinja2 템플릿 엔진을 사용하는 것이 좋다.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>FastAPI HTML 응답</title>
        <style>
            body { font-family: 'Apple SD Gothic Neo', sans-serif; margin: 40px; }
            h1 { color: #009688; }
            p { color: #333; line-height: 1.6; }
        </style>
    </head>
    <body>
        <h1>FastAPI HTML 응답 예제</h1>
        <p>이 페이지는 <strong>HTMLResponse</strong>를 사용하여 반환되었습니다.</p>
        <p>API 문서는 <a href="/docs">/docs</a>에서 확인할 수 있습니다.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ============================================================
# 8. RedirectResponse - 리다이렉트 응답
# ============================================================


@app.get(
    "/redirect",
    response_class=RedirectResponse,
    summary="다른 URL로 리다이렉트",
    tags=["응답 타입"],
)
def redirect_to_docs():
    """
    RedirectResponse를 사용하여 다른 URL로 리다이렉트한다.

    - 기본 상태 코드는 307 (Temporary Redirect)이다.
    - 영구 리다이렉트에는 status_code=301을 사용한다.
    - 이 예제에서는 Swagger UI 문서 페이지로 리다이렉트한다.
    """
    return RedirectResponse(url="/docs")


@app.get(
    "/old-endpoint",
    summary="영구 리다이렉트 (301)",
    tags=["응답 타입"],
)
def permanent_redirect():
    """
    301 Moved Permanently로 영구 리다이렉트한다.

    - **status_code=301**: 해당 URL이 영구적으로 이동했음을 나타낸다.
    - 검색 엔진이 이 정보를 인덱싱에 활용한다.
    """
    return RedirectResponse(
        url="/items/",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )


# ============================================================
# 9. PlainTextResponse - 일반 텍스트 응답
# ============================================================


@app.get(
    "/health",
    response_class=PlainTextResponse,
    summary="헬스 체크 (텍스트 응답)",
    tags=["응답 타입"],
)
def health_check():
    """
    PlainTextResponse를 사용하여 일반 텍스트를 반환한다.

    - 헬스 체크, 상태 확인 등 단순 텍스트 응답에 적합하다.
    - Content-Type이 text/plain으로 설정된다.
    """
    return PlainTextResponse(content="OK")


# ============================================================
# 10. response_model_exclude_unset - 설정되지 않은 기본값 제외
# ============================================================


@app.get(
    "/items/",
    response_model=list[ItemResponse],
    response_model_exclude_unset=True,
    summary="상품 목록 조회 (unset 필드 제외)",
    tags=["상품"],
)
def list_items():
    """
    모든 상품을 조회한다. 설정되지 않은 필드는 응답에서 제외된다.

    - **response_model_exclude_unset=True**: 명시적으로 설정하지 않은 기본값 필드를 제외한다.
    - 예: description이 None(기본값)인 경우 응답에 포함되지 않는다.
    - 클라이언트가 "값을 설정하지 않음"과 "명시적으로 None을 설정함"을 구분할 수 있다.
    """
    return list(items_db.values())
