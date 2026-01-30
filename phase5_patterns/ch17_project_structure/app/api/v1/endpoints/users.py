"""
사용자 API 엔드포인트 모듈

사용자 리소스에 대한 HTTP 엔드포인트를 정의한다.
라우터는 요청을 받아 입력을 검증한 뒤, CRUD 계층에 처리를 위임한다.
비즈니스 로직은 이 파일에 두지 않고, CRUD 또는 서비스 계층에 분리한다.

계층 구조에서의 위치:
    Client -> Router(이 모듈) -> CRUD -> 데이터 저장소
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.crud import user as user_crud

# 사용자 라우터 생성
# prefix: 이 라우터의 모든 경로에 "/users" 접두사가 붙는다
# tags: Swagger UI에서 엔드포인트를 그룹화할 태그
router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="전체 사용자 목록 조회",
    description="등록된 모든 사용자의 목록을 반환한다.",
)
async def get_users():
    """
    전체 사용자 목록을 조회하는 엔드포인트

    Returns:
        등록된 모든 사용자 리스트
    """
    return user_crud.get_all_users()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 생성",
    description="새로운 사용자를 생성하고, 생성된 사용자 정보를 반환한다.",
)
async def create_user(user_in: UserCreate):
    """
    새로운 사용자를 생성하는 엔드포인트

    Args:
        user_in: 사용자 생성 요청 데이터 (username, email, password)

    Returns:
        생성된 사용자 정보 (비밀번호 제외)
    """
    user = user_crud.create_user(user_in)
    return user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="특정 사용자 조회",
    description="ID를 기반으로 특정 사용자의 정보를 조회한다.",
)
async def get_user(user_id: int):
    """
    특정 사용자를 ID로 조회하는 엔드포인트

    Args:
        user_id: 조회할 사용자의 고유 ID

    Returns:
        해당 사용자 정보

    Raises:
        HTTPException(404): 사용자를 찾을 수 없는 경우
    """
    user = user_crud.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.",
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="사용자 정보 수정",
    description="기존 사용자의 정보를 수정한다. 전달된 필드만 업데이트된다.",
)
async def update_user(user_id: int, user_in: UserUpdate):
    """
    사용자 정보를 수정하는 엔드포인트

    Args:
        user_id: 수정할 사용자의 고유 ID
        user_in: 수정할 데이터 (변경할 필드만 전송 가능)

    Returns:
        수정된 사용자 정보

    Raises:
        HTTPException(404): 사용자를 찾을 수 없는 경우
    """
    user = user_crud.update_user(user_id, user_in)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.",
        )
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="사용자 삭제",
    description="ID를 기반으로 사용자를 삭제한다.",
)
async def delete_user(user_id: int):
    """
    사용자를 삭제하는 엔드포인트

    Args:
        user_id: 삭제할 사용자의 고유 ID

    Raises:
        HTTPException(404): 사용자를 찾을 수 없는 경우
    """
    deleted = user_crud.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.",
        )
    # 204 응답은 본문(body)을 반환하지 않는다
    return None
