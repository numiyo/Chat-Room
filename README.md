# Realtime Chat with DeepSeek Bot

基于 **FastAPI \+ WebSocket** 的实时多人聊天室，内置可配置的 DeepSeek 聊天机器人。需注册 DeepSeek 开放平台并配置 API Key，部署即可使用。

## 功能

- 匿名聊天（支持自定义昵称）

- 实时消息收发，支持回车键发送消息

- 系统自动广播用户加入 / 离开通知

- 自动回复机器人：所有用户消息均可获得 DeepSeek 模型自动回复（无需触发词）

- 成本友好：默认使用低成本模型，严格限制回复长度

## 项目结构

```Plain Text
Chat-Room/
├── app.py          # 主程序（FastAPI + WebSocket + 前端页面 + 机器人逻辑）
├── requirements.txt # Python 依赖包列表
├── update.sh       # 一键部署/更新脚本
├── api_key.txt     # DeepSeek API Key（需手动填写）
├── prompt.txt      # 机器人系统提示词（可自定义）
├── model.txt       # 模型名称配置（默认 deepseek-v4-flash）
└── README.md       # 项目说明文档
```

## 快速部署（Linux 服务器）

### 1\. 克隆仓库

```bash
git clone https://github.com/numiyo/Chat-Room.git
cd Chat-Room
```

### 2\. 配置 API Key

编辑 `api_key.txt`，填入你的 DeepSeek API Key：

```Plain Text
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

可选配置：

- 自定义机器人人设：编辑 `prompt.txt`

- 切换模型版本：将 `model.txt` 内容修改为 `deepseek-v4-pro`

### 3\. 一键启动服务

```bash
chmod +x update.sh
./update.sh
```

服务默认监听 `8080` 端口，访问地址：

```Plain Text
http://服务器公网IP:8080
```

## 配置文件说明

| 文件名称        | 用途              | 默认值                                                    |
| --------------- | ----------------- | --------------------------------------------------------- |
| `api_key.txt` | DeepSeek API 密钥 | 无（必填项）                                              |
| `prompt.txt`   | 机器人系统提示词  | 你是一个友好、幽默的聊天助手，请用简短的中文回复。        |
| `model.txt`    | 大模型名称        | `deepseek-v4-flash`（低成本），可选 `deepseek-v4-pro` |

## 机器人成本控制

- 默认最大回复 Token 数：`300`（可在 `app.py` 中修改 `MAX_BOT_TOKENS` 参数）

- 采用异步 API 调用，不阻塞用户消息收发

## 服务更新

代码更新后，执行一键更新脚本：

```bash
./update.sh
```

脚本会自动终止旧进程、安装依赖并重启服务。

## 技术栈

- **后端**：Python 3\.7\+ / FastAPI / Uvicorn

- **实时通信**：WebSocket

- **机器人接口**：DeepSeek API（基于 httpx 异步调用）

- **前端**：原生 HTML \+ CSS \+ JavaScript
