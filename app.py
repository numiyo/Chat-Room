from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict
import httpx
import asyncio

app = FastAPI()

# ---------- 读取配置文件 ----------
def load_config(filename: str, default: str = "") -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return default

API_KEY = load_config("api_key.txt")
SYSTEM_PROMPT = load_config("prompt.txt", "你是一个友好、幽默的聊天助手，请用简短的中文回复。")
MODEL_NAME = load_config("model.txt", "deepseek-v4-flash")   # 可以换deepseek-v4-pro

# 机器人是否可用
BOT_ENABLED = bool(API_KEY)
BOT_NAME = "常用中文机器人名"

# 成本控制：最大回复 token 数
MAX_BOT_TOKENS = 300

# ---------- 连接管理器 ----------
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        try:
            data = await websocket.receive_json()
            if data.get("type") == "join":
                username = data.get("username", "").strip() or "匿名"
                self.active_connections[websocket] = username
                await self.broadcast({
                    "type": "system",
                    "message": f"{username} 加入了聊天室"
                })
            else:
                await websocket.close()
        except Exception:
            await websocket.close()

    def disconnect(self, websocket: WebSocket):
        return self.active_connections.pop(websocket, None) or "未知用户"

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections.keys()):
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# ---------- 调用 DeepSeek API ----------
async def get_bot_reply(user_message: str, username: str) -> str | None:
    """异步获取机器人回复，失败返回 None"""
    if not BOT_ENABLED:
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{username}: {user_message}"}
    ]
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": MAX_BOT_TOKENS,
        "temperature": 0.7
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                json=payload,
                headers=headers
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"Bot API error: {resp.status_code} {resp.text}")
                return None
    except Exception as e:
        print(f"Bot request failed: {e}")
        return None

# ---------- 前端页面 ----------
@app.get("/", response_class=HTMLResponse)
async def get():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>实时聊天室</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; max-width: 600px; }
        #messages {
            border: 1px solid #aaa; height: 300px; overflow-y: scroll;
            padding: 10px; margin-bottom: 10px; background: #fafafa;
        }
        .system { color: #888; font-style: italic; margin: 4px 0; }
        .chat { margin: 4px 0; }
        .bot { color: #e67e22; }
        .username { font-weight: bold; color: #2c3e50; }
        #loginBox, #chatBox { margin-bottom: 10px; }
        input[type="text"] { padding: 6px; width: 200px; }
        button { padding: 6px 12px; }
    </style>
</head>
<body>
    <h2>简易聊天室</h2>
    <div id="loginBox">
        <input type="text" id="usernameInput" placeholder="输入昵称（可选）" />
        <button onclick="join()">加入聊天</button>
    </div>
    <div id="chatBox" style="display:none;">
        <div id="messages"></div>
        <input type="text" id="messageInput" placeholder="输入消息..." onkeypress="handleKey(event)" />
        <button onclick="sendMessage()">发送</button>
        <button onclick="leave()">离开</button>
    </div>

    <script>
        let ws = null;

        function join() {
            const username = document.getElementById('usernameInput').value.trim();
            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${location.host}/ws`);

            ws.onopen = () => {
                ws.send(JSON.stringify({ type: 'join', username }));
                document.getElementById('loginBox').style.display = 'none';
                document.getElementById('chatBox').style.display = 'block';
                document.getElementById('messageInput').focus();
            };

            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                const div = document.createElement('div');
                if (msg.type === 'system') {
                    div.className = 'system';
                    div.textContent = msg.message;
                } else if (msg.type === 'chat') {
                    div.className = 'chat';
                    if (msg.isBot) div.classList.add('bot');
                    div.innerHTML = `<span class="username">${msg.username}:</span> ${msg.message}`;
                }
                const box = document.getElementById('messages');
                box.appendChild(div);
                box.scrollTop = box.scrollHeight;
            };

            ws.onclose = () => {
                document.getElementById('loginBox').style.display = 'block';
                document.getElementById('chatBox').style.display = 'none';
            };

            ws.onerror = () => alert('连接出错，请刷新重试');
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            if (text && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'chat', message: text }));
                input.value = '';
                input.focus();
            }
        }

        function handleKey(e) { if (e.key === 'Enter') sendMessage(); }
        function leave() { if (ws) ws.close(); }
    </script>
</body>
</html>
""")

# ---------- WebSocket 端点 ----------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "chat":
                username = manager.active_connections.get(websocket, "未知")
                # 广播用户消息
                await manager.broadcast({
                    "type": "chat",
                    "username": username,
                    "message": data["message"]
                })

                # 异步调用机器人，不阻塞其他消息
                asyncio.create_task(handle_bot_reply(data["message"], username))

    except WebSocketDisconnect:
        username = manager.disconnect(websocket)
        await manager.broadcast({
            "type": "system",
            "message": f"{username} 离开了聊天室"
        })
    except Exception:
        username = manager.disconnect(websocket)
        await manager.broadcast({
            "type": "system",
            "message": f"{username} 离开了聊天室"
        })

async def handle_bot_reply(user_message: str, username: str):
    """独立任务：获取机器人回复并广播"""
    bot_reply = await get_bot_reply(user_message, username)
    if bot_reply:
        await manager.broadcast({
            "type": "chat",
            "username": BOT_NAME,
            "message": bot_reply,
            "isBot": True
        })