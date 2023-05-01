from typing import Any
from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import HTMLResponse
from celery.result import AsyncResult

from app import models, schemas
from app.api import deps
from app.core.celery_app import celery_app
from cache import Cache


router = APIRouter()


@router.post("/test-celery/", response_model=schemas.Msg, status_code=201)
def test_celery(
    msg: schemas.Msg,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Test Celery worker.
    """
    task = celery_app.send_task("app.worker.test_celery", args=[msg.msg])
    return {
        "msg": f"{msg.msg} - {task.id}",
    }


@router.get("/test-redis/", status_code=201)
async def test_redis(
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Test redis connection.
    """
    try:
        redis_cache = Cache()
        if redis_cache.connected:
            return {"msg": "Redis connection works."}
    except Exception as e:
        return {"msg": f"ERROR: {str(e)}"}


@router.websocket("/echo-client/")
async def echo_client(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("{::address::}");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@router.get("/test-websocket/")
async def test_websocket(address: str):
    return HTMLResponse(html.replace("{::address::}", address))
