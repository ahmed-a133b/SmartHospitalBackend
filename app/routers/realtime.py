# routers/realtime.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
clients = []

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Just to keep connection alive
    except WebSocketDisconnect:
        clients.remove(websocket)

# Broadcast function for external use
async def broadcast_message(message: str):
    for ws in clients:
        try:
            await ws.send_text(message)
        except:
            clients.remove(ws)
