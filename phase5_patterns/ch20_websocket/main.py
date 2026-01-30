"""
Chapter 20: WebSocket

FastAPI의 WebSocket 엔드포인트를 사용하여
실시간 양방향 통신(채팅)을 구현한다.

핵심 구성:
- ConnectionManager: 다중 클라이언트 연결 관리
- WebSocket 엔드포인트: 메시지 수신 및 브로드캐스트
- HTML 클라이언트 제공: 채팅 UI 페이지

실행 방법:
    uvicorn main:app --reload
    브라우저에서 http://localhost:8000 접속
"""

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

# ============================================================
# FastAPI 앱 인스턴스 생성
# ============================================================
app = FastAPI(
    title="WebSocket 채팅 API",
    description="WebSocket을 사용한 실시간 채팅 예제",
    version="1.0.0",
)


# ============================================================
# ConnectionManager 클래스
#
# WebSocket 연결을 중앙에서 관리하는 매니저 패턴.
# 연결/해제/개인 메시지/브로드캐스트 기능을 캡슐화한다.
# ============================================================
class ConnectionManager:
    """
    WebSocket 연결 관리자.

    다수의 클라이언트 연결을 추적하고,
    메시지 전송 기능을 제공한다.
    """

    def __init__(self):
        # 활성 연결 목록: (client_id, WebSocket) 쌍을 저장
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """
        새 WebSocket 연결을 수락하고 활성 연결 목록에 추가한다.

        Args:
            client_id: 클라이언트 고유 식별자
            websocket: WebSocket 연결 객체
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"[연결] {client_id} 접속 (현재 {len(self.active_connections)}명)")

    def disconnect(self, client_id: str) -> None:
        """
        클라이언트 연결을 해제하고 활성 연결 목록에서 제거한다.

        Args:
            client_id: 연결을 해제할 클라이언트 식별자
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        print(f"[해제] {client_id} 퇴장 (현재 {len(self.active_connections)}명)")

    async def send_personal_message(self, message: str, client_id: str) -> None:
        """
        특정 클라이언트에게 개인 메시지를 전송한다.

        Args:
            message: 전송할 메시지 내용
            client_id: 수신 대상 클라이언트 식별자
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str, exclude: str | None = None) -> None:
        """
        모든 연결된 클라이언트에게 메시지를 브로드캐스트한다.

        Args:
            message: 전송할 메시지 내용
            exclude: 제외할 클라이언트 ID (발신자 제외 시 사용, None이면 전체 전송)
        """
        # 연결 해제된 클라이언트를 추적하여 안전하게 제거
        disconnected: list[str] = []

        for client_id, websocket in self.active_connections.items():
            if client_id == exclude:
                continue
            try:
                await websocket.send_text(message)
            except Exception:
                # 전송 실패 시 해당 연결을 해제 대상에 추가
                disconnected.append(client_id)

        # 실패한 연결 제거
        for client_id in disconnected:
            self.disconnect(client_id)

    def get_online_users(self) -> list[str]:
        """현재 접속 중인 클라이언트 ID 목록을 반환한다."""
        return list(self.active_connections.keys())


# ConnectionManager 싱글톤 인스턴스 생성
manager = ConnectionManager()


# ============================================================
# HTML 클라이언트 페이지 제공 엔드포인트
# ============================================================
@app.get("/", response_class=HTMLResponse, summary="채팅 클라이언트 페이지")
async def get_chat_page():
    """
    WebSocket 채팅 클라이언트 HTML 페이지를 반환한다.

    같은 디렉토리의 client.html 파일을 읽어서 제공한다.
    """
    # client.html 파일 경로를 현재 스크립트 기준으로 설정
    html_path = Path(__file__).parent / "client.html"
    html_content = html_path.read_text(encoding="utf-8")
    return HTMLResponse(content=html_content)


# ============================================================
# WebSocket 엔드포인트
#
# 클라이언트가 ws://localhost:8000/ws/{client_id}로 연결하면
# 양방향 실시간 통신이 시작된다.
# ============================================================
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket 연결을 처리하는 메인 엔드포인트.

    흐름:
    1. 클라이언트 연결 수락 및 입장 알림 브로드캐스트
    2. 메시지 수신 대기 루프 (무한 루프)
    3. 수신한 메시지를 모든 클라이언트에게 브로드캐스트
    4. 연결 종료 시 퇴장 알림 브로드캐스트

    Args:
        websocket: WebSocket 연결 객체 (FastAPI가 자동 주입)
        client_id: URL 경로에서 추출한 클라이언트 식별자
    """
    # 1단계: 연결 수락
    await manager.connect(client_id, websocket)

    # 현재 시각을 포맷팅
    now = datetime.now().strftime("%H:%M:%S")

    # 입장 메시지를 모든 클라이언트에게 브로드캐스트
    await manager.broadcast(
        f"[{now}] 시스템: '{client_id}'님이 채팅에 참여했습니다. "
        f"(접속자 {len(manager.active_connections)}명)"
    )

    try:
        # 2단계: 메시지 수신 대기 루프
        # WebSocketDisconnect 예외가 발생할 때까지 계속 실행
        while True:
            # 클라이언트로부터 텍스트 메시지 수신 (비동기 대기)
            data = await websocket.receive_text()
            now = datetime.now().strftime("%H:%M:%S")

            # 수신한 메시지를 모든 클라이언트에게 브로드캐스트
            await manager.broadcast(f"[{now}] {client_id}: {data}")

    except WebSocketDisconnect:
        # 3단계: 클라이언트 연결 종료 처리
        # 브라우저 탭을 닫거나 네트워크가 끊어지면 이 예외가 발생한다
        manager.disconnect(client_id)
        now = datetime.now().strftime("%H:%M:%S")

        # 퇴장 메시지를 나머지 클라이언트에게 브로드캐스트
        await manager.broadcast(
            f"[{now}] 시스템: '{client_id}'님이 채팅에서 나갔습니다. "
            f"(접속자 {len(manager.active_connections)}명)"
        )


# ============================================================
# REST API 엔드포인트 (부가 기능)
# WebSocket과 함께 REST API도 제공할 수 있다.
# ============================================================
@app.get("/users/online", summary="현재 접속 중인 사용자 목록")
async def get_online_users():
    """현재 WebSocket으로 접속 중인 사용자 목록을 반환한다."""
    users = manager.get_online_users()
    return {
        "online_count": len(users),
        "users": users,
    }
