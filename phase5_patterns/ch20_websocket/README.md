# Chapter 20: WebSocket

## 학습 목표

- WebSocket 프로토콜의 개념과 HTTP와의 차이를 이해한다
- FastAPI에서 WebSocket 엔드포인트를 구현할 수 있다
- `ConnectionManager` 패턴을 사용하여 다중 클라이언트 연결을 관리할 수 있다
- 브로드캐스트(전체 전송)와 개인 메시지 전송을 구현할 수 있다
- HTML/JavaScript를 사용한 WebSocket 클라이언트를 작성할 수 있다

## 핵심 개념

### 1. WebSocket이란?

WebSocket은 클라이언트와 서버 간의 **양방향 실시간 통신**을 위한 프로토콜이다. HTTP와 달리 한 번 연결이 수립되면 양쪽에서 자유롭게 데이터를 주고받을 수 있다.

### 2. HTTP vs WebSocket

| 항목 | HTTP | WebSocket |
|------|------|-----------|
| 통신 방식 | 요청-응답 (단방향) | 양방향 (full-duplex) |
| 연결 유지 | 요청마다 새 연결 (또는 keep-alive) | 한 번 연결 후 지속 유지 |
| 프로토콜 | `http://` / `https://` | `ws://` / `wss://` |
| 사용 사례 | REST API, 웹 페이지 | 채팅, 실시간 알림, 게임 |
| 오버헤드 | 매 요청마다 헤더 전송 | 초기 핸드셰이크 후 최소 오버헤드 |
| 서버 푸시 | 불가 (폴링 필요) | 가능 |

### 3. FastAPI WebSocket 엔드포인트

FastAPI는 Starlette을 기반으로 WebSocket 엔드포인트를 지원한다.

```python
from fastapi import WebSocket

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()  # 연결 수락
    while True:
        data = await websocket.receive_text()  # 메시지 수신 대기
        await websocket.send_text(f"메시지 수신: {data}")  # 메시지 전송
```

### 4. ConnectionManager 패턴

다수의 WebSocket 클라이언트를 관리하기 위한 디자인 패턴이다. 연결, 해제, 개인 메시지, 브로드캐스트 등의 기능을 하나의 클래스에 캡슐화한다.

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
```

### 5. WebSocket 생명주기

```
클라이언트                     서버
    |                          |
    |--- 핸드셰이크 요청 ------->|
    |<-- 핸드셰이크 응답 --------|  (연결 수립)
    |                          |
    |<== 양방향 데이터 전송 ====>|  (메시지 교환)
    |                          |
    |--- 연결 종료 요청 -------->|
    |<-- 연결 종료 확인 ---------|  (연결 해제)
```

## 코드 실행 방법

### 사전 준비

```bash
pip install fastapi uvicorn
```

### 앱 실행

```bash
uvicorn main:app --reload
```

### 테스트 방법

1. 브라우저에서 `http://localhost:8000` 접속 (채팅 클라이언트 페이지)
2. 클라이언트 ID를 입력하고 연결
3. 다른 브라우저 탭에서도 접속하여 다중 클라이언트 테스트
4. 메시지를 입력하고 전송하면 모든 연결된 클라이언트에게 브로드캐스트

### Swagger UI

`http://localhost:8000/docs`에서 REST 엔드포인트 확인 가능 (WebSocket은 Swagger UI에서 테스트 불가)

## 실습 포인트

1. **기본 WebSocket 연결**: 브라우저에서 WebSocket 연결을 수립하고 메시지를 주고받는다
2. **브로드캐스트**: 여러 탭을 열어 한 클라이언트가 보낸 메시지가 모든 클라이언트에게 전달되는지 확인한다
3. **연결 해제 처리**: 탭을 닫을 때 다른 클라이언트에게 퇴장 메시지가 전송되는지 확인한다
4. **ConnectionManager**: 연결 관리 로직이 하나의 클래스에 캡슐화되어 있는 구조를 이해한다
5. **에러 처리**: 비정상 연결 종료(WebSocketDisconnect) 예외를 적절히 처리하는 방법을 확인한다

## 참고 자료

- [FastAPI 공식 문서 - WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [MDN - WebSocket API](https://developer.mozilla.org/ko/docs/Web/API/WebSocket)
- [WebSocket 프로토콜 RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)
