"""
Chapter 03 - Request Body와 Pydantic 모델
=========================================
Pydantic BaseModel, Field 검증, field_validator, 중첩 모델,
다중 Body 파라미터를 활용한 API 설계 예제.
"""

from typing import Optional

from fastapi import FastAPI, Body
from pydantic import BaseModel, Field, field_validator, model_validator

# ============================================================
# FastAPI 앱 인스턴스 생성
# ============================================================
app = FastAPI(
    title="Chapter 03 - Request Body & Pydantic",
    description="Pydantic 모델을 활용한 요청 본문 검증 예제 API",
    version="1.0.0",
)


# ============================================================
# 1. 기본 Pydantic 모델 - 아이템
# ============================================================
# BaseModel을 상속하면 해당 클래스의 인스턴스가 자동으로 검증된다.
# Field()를 사용하면 각 필드에 대한 세밀한 제약 조건을 설정할 수 있다.
class ItemCreate(BaseModel):
    """아이템 생성에 사용되는 요청 모델"""

    name: str = Field(
        ...,  # ... (Ellipsis)는 필수 필드임을 나타낸다
        min_length=1,   # 최소 1글자
        max_length=100,  # 최대 100글자
        title="아이템 이름",
        description="아이템의 이름 (1~100자)",
        examples=["노트북"],
    )
    price: float = Field(
        ...,
        gt=0,             # 0보다 커야 한다 (양수만 허용)
        le=100_000_000,   # 1억 원 이하
        title="가격",
        description="아이템의 가격 (원), 0 초과 ~ 1억 이하",
        examples=[1200000],
    )
    quantity: int = Field(
        default=1,       # 기본값 1 (선택적 필드)
        ge=1,            # 최소 1개
        le=9999,         # 최대 9999개
        title="수량",
        description="주문 수량 (1~9999)",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        title="설명",
        description="아이템에 대한 설명 (선택, 최대 500자)",
    )
    tags: list[str] = Field(
        default=[],
        title="태그",
        description="아이템 분류 태그 목록",
    )

    # --------------------------------------------------------
    # Pydantic v2 방식의 JSON 스키마 예제 설정
    # --------------------------------------------------------
    # Swagger UI의 "Example Value"에 표시되는 예제 데이터이다.
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "고성능 노트북",
                    "price": 1500000,
                    "quantity": 2,
                    "description": "M3 칩 탑재 노트북",
                    "tags": ["전자기기", "컴퓨터"],
                }
            ]
        }
    }


# ============================================================
# 2. Field Validator를 사용하는 모델 - 아이템 업데이트
# ============================================================
# field_validator를 사용하면 기본 타입 검증 이상의 커스텀 로직을 추가할 수 있다.
class ItemUpdate(BaseModel):
    """아이템 수정에 사용되는 요청 모델 (모든 필드 선택적)"""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        title="아이템 이름",
    )
    price: Optional[float] = Field(
        default=None,
        gt=0,
        le=100_000_000,
        title="가격",
    )
    discount_percent: Optional[float] = Field(
        default=None,
        ge=0,     # 0% 이상
        le=100,   # 100% 이하
        title="할인율 (%)",
        description="0~100 사이의 할인율",
    )
    tags: Optional[list[str]] = Field(
        default=None,
        title="태그",
    )

    # --------------------------------------------------------
    # field_validator: 태그 이름에 대한 커스텀 검증
    # --------------------------------------------------------
    # 각 태그가 비어있지 않은지, 공백만으로 이루어져 있지 않은지 검증한다.
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """태그 목록의 각 항목이 유효한지 검증한다."""
        if v is None:
            return v
        validated_tags = []
        for tag in v:
            # 앞뒤 공백 제거
            stripped = tag.strip()
            if not stripped:
                raise ValueError("빈 문자열은 태그로 사용할 수 없습니다")
            if len(stripped) > 30:
                raise ValueError(f"태그 '{stripped}'이(가) 30자를 초과합니다")
            validated_tags.append(stripped)
        return validated_tags

    # --------------------------------------------------------
    # model_validator: 모델 레벨의 교차 필드 검증
    # --------------------------------------------------------
    # 최소한 하나의 필드는 값이 있어야 업데이트가 의미가 있다.
    @model_validator(mode="after")
    def check_at_least_one_field(self):
        """최소한 하나의 필드에 값이 있는지 확인한다."""
        if all(
            getattr(self, field) is None
            for field in self.model_fields
        ):
            raise ValueError("최소한 하나의 필드에 값을 입력해야 합니다")
        return self


# ============================================================
# 3. 중첩 모델 - 주소와 사용자
# ============================================================
# 모델 안에 다른 모델을 필드로 포함하면 중첩(Nested) 구조가 된다.
# JSON에서는 중괄호 안에 중괄호가 들어가는 형태로 표현된다.

class Address(BaseModel):
    """주소 정보를 담는 중첩 모델"""

    city: str = Field(
        ...,
        min_length=1,
        max_length=50,
        title="도시",
        description="시/도 이름",
        examples=["서울"],
    )
    district: str = Field(
        ...,
        min_length=1,
        max_length=50,
        title="구/군",
        description="구/군 이름",
        examples=["강남구"],
    )
    street: str = Field(
        ...,
        min_length=1,
        max_length=200,
        title="도로명 주소",
        description="상세 도로명 주소",
        examples=["테헤란로 123"],
    )
    zip_code: str = Field(
        ...,
        title="우편번호",
        description="5자리 우편번호",
        examples=["06236"],
    )

    # --------------------------------------------------------
    # 우편번호 형식 검증 (5자리 숫자)
    # --------------------------------------------------------
    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: str) -> str:
        """우편번호가 5자리 숫자인지 검증한다."""
        stripped = v.strip()
        if not stripped.isdigit() or len(stripped) != 5:
            raise ValueError("우편번호는 5자리 숫자여야 합니다 (예: 06236)")
        return stripped


class UserCreate(BaseModel):
    """사용자 생성에 사용되는 요청 모델 (주소 중첩 포함)"""

    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        title="이름",
        description="사용자 이름 (2~50자)",
        examples=["홍길동"],
    )
    email: str = Field(
        ...,
        min_length=5,
        max_length=100,
        title="이메일",
        description="유효한 이메일 주소",
        examples=["hong@example.com"],
    )
    age: int = Field(
        ...,
        ge=0,     # 0세 이상
        le=150,   # 150세 이하
        title="나이",
        description="사용자 나이 (0~150)",
        examples=[30],
    )
    address: Address = Field(
        ...,
        title="주소",
        description="사용자의 주소 정보 (중첩 모델)",
    )
    phone: Optional[str] = Field(
        default=None,
        title="전화번호",
        description="연락처 (선택)",
        examples=["010-1234-5678"],
    )
    hobbies: list[str] = Field(
        default=[],
        title="취미",
        description="취미 목록",
    )

    # --------------------------------------------------------
    # 이메일 형식 검증
    # --------------------------------------------------------
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """이메일 형식이 올바른지 기본적으로 검증한다."""
        if "@" not in v:
            raise ValueError("이메일에는 '@' 기호가 포함되어야 합니다")
        local_part, _, domain = v.partition("@")
        if not local_part:
            raise ValueError("이메일의 '@' 앞부분이 비어있습니다")
        if "." not in domain:
            raise ValueError("이메일 도메인에 '.'이 포함되어야 합니다 (예: example.com)")
        # 소문자로 정규화하여 반환
        return v.lower().strip()

    # --------------------------------------------------------
    # 전화번호 형식 검증
    # --------------------------------------------------------
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """전화번호에서 하이픈을 제거한 뒤 숫자만 남기고 검증한다."""
        if v is None:
            return v
        # 하이픈, 공백 제거 후 숫자만 남긴다
        digits_only = v.replace("-", "").replace(" ", "")
        if not digits_only.isdigit():
            raise ValueError("전화번호는 숫자와 하이픈만 포함할 수 있습니다")
        if len(digits_only) < 10 or len(digits_only) > 11:
            raise ValueError("전화번호는 10~11자리 숫자여야 합니다")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "홍길동",
                    "email": "hong@example.com",
                    "age": 30,
                    "address": {
                        "city": "서울",
                        "district": "강남구",
                        "street": "테헤란로 123",
                        "zip_code": "06236",
                    },
                    "phone": "010-1234-5678",
                    "hobbies": ["독서", "등산"],
                }
            ]
        }
    }


# ============================================================
# 4. 주문 모델 - 여러 모델을 Body로 수신하기 위한 모델
# ============================================================
class OrderItem(BaseModel):
    """주문 항목 모델 (주문 내 개별 아이템)"""

    item_name: str = Field(..., min_length=1, max_length=100, title="아이템 이름")
    quantity: int = Field(..., ge=1, le=100, title="수량")
    unit_price: float = Field(..., gt=0, title="단가")


class OrderCreate(BaseModel):
    """주문 생성 모델"""

    items: list[OrderItem] = Field(
        ...,
        min_length=1,  # 최소 1개의 주문 항목 필요
        title="주문 항목 목록",
        description="주문할 아이템 목록 (최소 1개)",
    )
    shipping_address: Address = Field(
        ...,
        title="배송지 주소",
    )
    note: Optional[str] = Field(
        default=None,
        max_length=300,
        title="배송 메모",
        description="배송 시 요청사항 (선택, 최대 300자)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {"item_name": "노트북", "quantity": 1, "unit_price": 1500000},
                        {"item_name": "마우스", "quantity": 2, "unit_price": 35000},
                    ],
                    "shipping_address": {
                        "city": "서울",
                        "district": "서초구",
                        "street": "반포대로 45",
                        "zip_code": "06500",
                    },
                    "note": "부재시 경비실에 맡겨주세요",
                }
            ]
        }
    }


# ============================================================
# 인메모리 저장소 (학습용)
# ============================================================
# 실제로는 데이터베이스를 사용하지만, 학습 목적으로 딕셔너리에 저장한다.
items_db: dict[int, dict] = {}
users_db: dict[int, dict] = {}
orders_db: dict[int, dict] = {}

# ID 자동 증가를 위한 카운터
_item_id_counter = 0
_user_id_counter = 0
_order_id_counter = 0


# ============================================================
# 엔드포인트 1: 아이템 생성 (기본 모델)
# ============================================================
@app.post(
    "/items/",
    summary="아이템 생성",
    description="Pydantic 모델로 검증된 데이터를 받아 아이템을 생성한다.",
    tags=["아이템"],
    status_code=201,  # 생성 성공 시 201 Created 반환
)
def create_item(item: ItemCreate):
    """
    Request Body로 아이템 데이터를 수신하여 생성한다.

    - **name**: 아이템 이름 (필수, 1~100자)
    - **price**: 가격 (필수, 0 초과)
    - **quantity**: 수량 (선택, 기본값 1)
    - **description**: 설명 (선택)
    - **tags**: 태그 목록 (선택)

    Pydantic이 자동으로 타입 변환 및 검증을 수행한다.
    검증 실패 시 422 에러가 자동 반환된다.
    """
    global _item_id_counter
    _item_id_counter += 1

    # .model_dump()는 Pydantic v2에서 모델을 딕셔너리로 변환하는 메서드이다.
    # (Pydantic v1의 .dict()에 해당)
    item_dict = item.model_dump()
    item_dict["id"] = _item_id_counter

    # 총 금액을 계산하여 추가한다.
    item_dict["total_price"] = item.price * item.quantity

    # 인메모리 저장소에 저장
    items_db[_item_id_counter] = item_dict

    return {
        "message": "아이템이 성공적으로 생성되었습니다.",
        "item": item_dict,
    }


# ============================================================
# 엔드포인트 2: 아이템 수정 (Field Validator 활용)
# ============================================================
@app.put(
    "/items/{item_id}",
    summary="아이템 수정",
    description="field_validator가 포함된 모델로 아이템을 수정한다.",
    tags=["아이템"],
)
def update_item(item_id: int, item_update: ItemUpdate):
    """
    아이템 ID에 해당하는 아이템의 정보를 수정한다.

    - **item_id**: 수정할 아이템 ID (Path 파라미터)
    - **item_update**: 수정할 필드 (최소 1개 필수, model_validator로 검증)

    field_validator로 태그 유효성을 검증하고,
    model_validator로 최소 하나의 필드에 값이 있는지 확인한다.
    """
    if item_id not in items_db:
        return {"message": f"item_id={item_id}에 해당하는 아이템이 없습니다."}

    # exclude_unset=True: 클라이언트가 명시적으로 보낸 필드만 포함한다.
    # (기본값이 적용된 필드는 제외)
    update_data = item_update.model_dump(exclude_unset=True)

    # 기존 데이터에 변경된 필드만 덮어씌운다.
    for key, value in update_data.items():
        items_db[item_id][key] = value

    # 가격이 변경되었으면 총 금액도 재계산한다.
    stored = items_db[item_id]
    if "price" in update_data or "quantity" in stored:
        stored["total_price"] = stored.get("price", 0) * stored.get("quantity", 1)

    return {
        "message": "아이템이 성공적으로 수정되었습니다.",
        "item": stored,
    }


# ============================================================
# 엔드포인트 3: 사용자 생성 (중첩 모델)
# ============================================================
@app.post(
    "/users/",
    summary="사용자 생성",
    description="중첩 모델(Address)이 포함된 사용자를 생성한다.",
    tags=["사용자"],
    status_code=201,
)
def create_user(user: UserCreate):
    """
    Request Body로 사용자 데이터를 수신하여 생성한다.

    - **name**: 이름 (필수, 2~50자)
    - **email**: 이메일 (필수, field_validator로 형식 검증)
    - **age**: 나이 (필수, 0~150)
    - **address**: 주소 (필수, Address 중첩 모델)
    - **phone**: 전화번호 (선택, field_validator로 형식 검증)
    - **hobbies**: 취미 목록 (선택)

    Address 모델 내부의 zip_code도 자동으로 검증된다.
    """
    global _user_id_counter
    _user_id_counter += 1

    user_dict = user.model_dump()
    user_dict["id"] = _user_id_counter

    users_db[_user_id_counter] = user_dict

    return {
        "message": "사용자가 성공적으로 생성되었습니다.",
        "user": user_dict,
    }


# ============================================================
# 엔드포인트 4: 사용자 목록 조회
# ============================================================
@app.get(
    "/users/",
    summary="사용자 목록 조회",
    description="등록된 전체 사용자 목록을 반환한다.",
    tags=["사용자"],
)
def list_users():
    """등록된 전체 사용자 목록을 반환한다."""
    return {
        "total": len(users_db),
        "users": list(users_db.values()),
    }


# ============================================================
# 엔드포인트 5: 주문 생성 (리스트 + 중첩 모델 조합)
# ============================================================
@app.post(
    "/orders/",
    summary="주문 생성",
    description="여러 주문 항목(OrderItem 리스트)과 배송지(Address)를 포함하는 주문을 생성한다.",
    tags=["주문"],
    status_code=201,
)
def create_order(order: OrderCreate):
    """
    주문 데이터를 수신하여 생성한다.

    - **items**: 주문 항목 리스트 (필수, 최소 1개)
      - 각 항목: item_name, quantity, unit_price
    - **shipping_address**: 배송지 주소 (필수, Address 중첩 모델)
    - **note**: 배송 메모 (선택)

    리스트와 중첩 모델이 함께 사용되는 복합 구조이다.
    """
    global _order_id_counter
    _order_id_counter += 1

    order_dict = order.model_dump()
    order_dict["id"] = _order_id_counter

    # 각 항목의 소계와 총 금액을 계산한다.
    total_amount = 0
    for item in order_dict["items"]:
        subtotal = item["quantity"] * item["unit_price"]
        item["subtotal"] = subtotal
        total_amount += subtotal

    order_dict["total_amount"] = total_amount
    order_dict["status"] = "주문 접수"

    orders_db[_order_id_counter] = order_dict

    return {
        "message": "주문이 성공적으로 생성되었습니다.",
        "order": order_dict,
    }


# ============================================================
# 엔드포인트 6: Body로 여러 모델을 동시에 수신
# ============================================================
# Body()를 사용하면 여러 개의 Pydantic 모델 및 단순 값을 하나의
# 엔드포인트에서 동시에 수신할 수 있다.
# 이 경우 각 파라미터 이름이 JSON의 키가 된다.
@app.post(
    "/items-with-user/",
    summary="아이템 + 사용자 동시 수신",
    description="하나의 요청에서 아이템과 사용자 데이터를 동시에 수신하는 예제이다.",
    tags=["복합"],
    status_code=201,
)
def create_item_with_user(
    item: ItemCreate,
    user: UserCreate,
    importance: int = Body(
        ...,
        ge=1,
        le=5,
        title="중요도",
        description="1(낮음) ~ 5(높음) 사이의 중요도",
        examples=[3],
    ),
    memo: str = Body(
        default="",
        max_length=200,
        title="메모",
        description="추가 메모 (선택)",
    ),
):
    """
    여러 모델과 단순 Body 값을 동시에 수신하는 예제이다.

    요청 JSON 구조:
    ```json
    {
        "item": { ... },
        "user": { ... },
        "importance": 3,
        "memo": "긴급 처리 요망"
    }
    ```

    - **item**: 아이템 데이터 (ItemCreate 모델)
    - **user**: 사용자 데이터 (UserCreate 모델)
    - **importance**: 중요도 (1~5, 필수)
    - **memo**: 메모 (선택)
    """
    global _item_id_counter, _user_id_counter
    _item_id_counter += 1
    _user_id_counter += 1

    item_dict = item.model_dump()
    item_dict["id"] = _item_id_counter

    user_dict = user.model_dump()
    user_dict["id"] = _user_id_counter

    items_db[_item_id_counter] = item_dict
    users_db[_user_id_counter] = user_dict

    return {
        "message": "아이템과 사용자가 함께 생성되었습니다.",
        "item": item_dict,
        "user": user_dict,
        "importance": importance,
        "memo": memo,
    }


# ============================================================
# 엔드포인트 7: 아이템 목록 조회 (생성된 데이터 확인용)
# ============================================================
@app.get(
    "/items/",
    summary="아이템 목록 조회",
    description="등록된 전체 아이템 목록을 반환한다.",
    tags=["아이템"],
)
def list_items():
    """등록된 전체 아이템 목록을 반환한다."""
    return {
        "total": len(items_db),
        "items": list(items_db.values()),
    }


# ============================================================
# 직접 실행 시 uvicorn으로 서버를 시작한다.
# ============================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
