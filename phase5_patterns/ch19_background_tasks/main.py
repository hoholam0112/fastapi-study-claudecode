"""
Chapter 19: 백그라운드 태스크 (Background Tasks)

FastAPI의 BackgroundTasks를 사용하여
응답 반환 후 백그라운드에서 작업을 수행하는 방법을 학습한다.

사용 사례:
- 로그 파일 기록
- 이메일/알림 발송 시뮬레이션
- 다중 백그라운드 태스크 등록

실행 방법:
    uvicorn main:app --reload
"""

import time
from datetime import datetime

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field

# ============================================================
# FastAPI 앱 인스턴스 생성
# ============================================================
app = FastAPI(
    title="백그라운드 태스크 학습 API",
    description="BackgroundTasks를 활용한 비동기 작업 처리 예제",
    version="1.0.0",
)

# ============================================================
# 인메모리 데이터 저장소
# ============================================================
items_db: dict[int, dict] = {}
_id_counter: int = 0

# 알림 발송 기록을 저장하는 리스트 (실습 확인용)
notification_log: list[dict] = []


# ============================================================
# Pydantic 모델 정의
# ============================================================
class ItemCreate(BaseModel):
    """아이템 생성 요청 모델"""

    name: str = Field(..., min_length=1, description="아이템 이름")
    price: float = Field(..., gt=0, description="아이템 가격")


class ItemResponse(BaseModel):
    """아이템 응답 모델"""

    id: int
    name: str
    price: float


# ============================================================
# 백그라운드 태스크 함수들
#
# 이 함수들은 엔드포인트에서 직접 호출되지 않고,
# BackgroundTasks.add_task()를 통해 등록되어
# 응답 반환 후 백그라운드에서 실행된다.
# ============================================================
def write_log(message: str) -> None:
    """
    로그 메시지를 파일에 기록하는 백그라운드 함수.

    응답이 클라이언트에게 반환된 후 실행되므로,
    파일 I/O로 인한 응답 지연이 발생하지 않는다.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"

    # 로그 파일에 추가 모드로 기록
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)

    print(f"[로그 기록 완료] {log_entry.strip()}")


def send_notification(email: str, message: str) -> None:
    """
    알림 발송을 시뮬레이션하는 백그라운드 함수.

    실제로는 이메일 발송, 푸시 알림 등의 작업이 수행되지만,
    여기서는 time.sleep()으로 느린 외부 API 호출을 시뮬레이션한다.

    이 함수가 3초간 대기하더라도,
    클라이언트는 즉시 응답을 받을 수 있다.
    """
    print(f"[알림 발송 시작] {email}에게 알림 전송 중...")

    # 외부 이메일/SMS API 호출을 시뮬레이션 (3초 소요)
    time.sleep(3)

    # 발송 기록 저장
    record = {
        "email": email,
        "message": message,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "발송 완료",
    }
    notification_log.append(record)

    print(f"[알림 발송 완료] {email} -> {message}")


def update_item_statistics(item_name: str) -> None:
    """
    아이템 통계를 업데이트하는 백그라운드 함수.

    실제로는 분석 서비스에 데이터를 전송하거나
    통계 테이블을 갱신하는 작업이 수행된다.
    """
    time.sleep(1)  # 통계 처리 시뮬레이션
    print(f"[통계 업데이트 완료] 아이템 '{item_name}' 통계 반영됨")


# ============================================================
# API 엔드포인트 정의
# ============================================================
@app.post(
    "/items/",
    response_model=ItemResponse,
    status_code=201,
    summary="아이템 생성 (백그라운드 로그 기록)",
)
def create_item(item: ItemCreate, background_tasks: BackgroundTasks):
    """
    새 아이템을 생성하고, 백그라운드에서 로그를 기록한다.

    흐름:
    1. 아이템을 인메모리 DB에 저장한다
    2. 응답을 클라이언트에게 즉시 반환한다
    3. 백그라운드에서 로그 파일에 생성 기록을 남긴다

    BackgroundTasks 파라미터는 FastAPI가 자동으로 주입한다.
    """
    global _id_counter
    _id_counter += 1
    item_id = _id_counter

    # 아이템 저장
    items_db[item_id] = {
        "id": item_id,
        "name": item.name,
        "price": item.price,
    }

    # 백그라운드 태스크 등록: 로그 기록
    # add_task(함수, *인자) 형식으로 등록한다
    background_tasks.add_task(
        write_log,
        f"아이템 생성됨 - ID: {item_id}, 이름: {item.name}, 가격: {item.price}원",
    )

    # 응답은 즉시 반환됨 (로그 기록은 백그라운드에서 수행)
    return items_db[item_id]


@app.post(
    "/send-notification/{email}",
    summary="알림 발송 (백그라운드 처리)",
)
def send_email_notification(email: str, background_tasks: BackgroundTasks):
    """
    지정된 이메일로 알림을 백그라운드에서 발송한다.

    실제 알림 발송은 3초가 소요되지만,
    클라이언트는 즉시 응답을 받는다.
    이것이 백그라운드 태스크의 핵심 장점이다.
    """
    message = f"{email}님, 새로운 업데이트가 있습니다!"

    # 백그라운드 태스크 등록: 알림 발송
    background_tasks.add_task(send_notification, email, message)

    # 알림 발송이 완료되기 전에 즉시 응답 반환
    return {
        "message": f"{email}로 알림이 발송 예정입니다",
        "status": "백그라운드 처리 중",
    }


@app.post(
    "/items-with-notification/",
    response_model=ItemResponse,
    status_code=201,
    summary="아이템 생성 + 다중 백그라운드 태스크",
)
def create_item_with_notification(
    item: ItemCreate,
    background_tasks: BackgroundTasks,
):
    """
    아이템을 생성하고 여러 백그라운드 태스크를 동시에 등록한다.

    하나의 엔드포인트에서 add_task()를 여러 번 호출하여
    다수의 백그라운드 작업을 등록할 수 있다.
    등록된 태스크들은 순차적으로 실행된다.

    등록되는 백그라운드 태스크:
    1. 로그 파일에 생성 기록
    2. 관리자에게 알림 발송
    3. 아이템 통계 업데이트
    """
    global _id_counter
    _id_counter += 1
    item_id = _id_counter

    # 아이템 저장
    items_db[item_id] = {
        "id": item_id,
        "name": item.name,
        "price": item.price,
    }

    # 백그라운드 태스크 1: 로그 기록
    background_tasks.add_task(
        write_log,
        f"아이템 생성됨 (알림 포함) - ID: {item_id}, 이름: {item.name}",
    )

    # 백그라운드 태스크 2: 관리자에게 알림 발송
    background_tasks.add_task(
        send_notification,
        "admin@example.com",
        f"새 아이템 '{item.name}'이(가) 등록되었습니다 (가격: {item.price}원)",
    )

    # 백그라운드 태스크 3: 통계 업데이트
    background_tasks.add_task(update_item_statistics, item.name)

    return items_db[item_id]


@app.get(
    "/items/",
    response_model=list[ItemResponse],
    summary="전체 아이템 목록 조회",
)
def read_items():
    """저장된 모든 아이템 목록을 반환한다."""
    return list(items_db.values())


@app.get(
    "/notifications/",
    summary="알림 발송 기록 조회",
)
def read_notification_log():
    """
    백그라운드에서 발송된 알림 기록을 조회한다.

    이 엔드포인트를 통해 백그라운드 태스크가
    실제로 실행되었는지 확인할 수 있다.
    """
    return {
        "total": len(notification_log),
        "notifications": notification_log,
    }
