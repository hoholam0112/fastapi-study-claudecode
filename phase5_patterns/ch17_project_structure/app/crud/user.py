"""
사용자 CRUD 모듈

데이터 저장소에 대한 생성(Create), 조회(Read), 수정(Update), 삭제(Delete) 로직을 담당한다.
이 데모에서는 인메모리 딕셔너리를 사용하지만,
실제 프로젝트에서는 SQLAlchemy 세션을 통해 데이터베이스와 상호작용한다.

계층 구조에서의 위치:
    Router(엔드포인트) -> CRUD(이 모듈) -> Model(데이터베이스)
    라우터는 직접 데이터를 조작하지 않고, CRUD 함수를 호출하여 처리한다.
"""

from app.schemas.user import UserCreate, UserUpdate, UserResponse


# 인메모리 데이터 저장소 (데모용)
# 실제 프로젝트에서는 데이터베이스 세션을 사용한다
_users_db: dict[int, dict] = {}

# 자동 증가 ID (데모용)
_next_id: int = 1


def get_all_users() -> list[UserResponse]:
    """
    전체 사용자 목록을 조회한다.

    Returns:
        모든 사용자의 UserResponse 리스트
    """
    return [UserResponse(**user_data) for user_data in _users_db.values()]


def get_user_by_id(user_id: int) -> UserResponse | None:
    """
    ID로 특정 사용자를 조회한다.

    Args:
        user_id: 조회할 사용자의 고유 ID

    Returns:
        사용자가 존재하면 UserResponse, 없으면 None
    """
    user_data = _users_db.get(user_id)
    if user_data is None:
        return None
    return UserResponse(**user_data)


def create_user(user_in: UserCreate) -> UserResponse:
    """
    새로운 사용자를 생성한다.

    Args:
        user_in: 사용자 생성에 필요한 데이터 (UserCreate 스키마)

    Returns:
        생성된 사용자 정보 (UserResponse)
    """
    global _next_id

    # 새 사용자 데이터를 구성한다
    # 실제 프로젝트에서는 비밀번호를 해시 처리하여 저장한다
    user_data = {
        "id": _next_id,
        "username": user_in.username,
        "email": user_in.email,
        "is_active": True,
    }

    # 인메모리 저장소에 저장한다
    _users_db[_next_id] = user_data

    # ID를 증가시킨다
    _next_id += 1

    return UserResponse(**user_data)


def update_user(user_id: int, user_in: UserUpdate) -> UserResponse | None:
    """
    기존 사용자 정보를 수정한다.

    전달된 필드 중 None이 아닌 값만 업데이트한다 (부분 수정 지원).

    Args:
        user_id: 수정할 사용자의 고유 ID
        user_in: 수정할 데이터 (UserUpdate 스키마)

    Returns:
        수정된 사용자 정보 (UserResponse), 사용자가 없으면 None
    """
    if user_id not in _users_db:
        return None

    # 기존 데이터를 가져온다
    stored_data = _users_db[user_id]

    # None이 아닌 필드만 업데이트한다 (exclude_unset=True 활용)
    update_data = user_in.model_dump(exclude_unset=True)

    # password 필드는 저장소에 직접 저장하지 않는다
    # 실제 프로젝트에서는 해시 처리 후 hashed_password로 저장한다
    update_data.pop("password", None)

    stored_data.update(update_data)
    _users_db[user_id] = stored_data

    return UserResponse(**stored_data)


def delete_user(user_id: int) -> bool:
    """
    사용자를 삭제한다.

    Args:
        user_id: 삭제할 사용자의 고유 ID

    Returns:
        삭제 성공 여부 (True: 삭제됨, False: 해당 사용자 없음)
    """
    if user_id not in _users_db:
        return False

    del _users_db[user_id]
    return True
