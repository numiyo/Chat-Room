#!/bin/bash

# 更新聊天室服务脚本
set -e

echo "=== 开始更新聊天室服务 ==="

# 1. 进入项目目录
cd /home/chat

# 2. 停止占用 8080 端口的旧进程（如果有）
OLD_PID=$(lsof -t -i:8080)
if [ -n "$OLD_PID" ]; then
    echo "停止旧进程 PID: $OLD_PID"
    kill -9 $OLD_PID
    sleep 1
fi

# 3. 如果使用 Git 拉取最新代码，取消下面一行的注释
# git pull

# 4. 安装/更新依赖
echo "安装/更新依赖..."
pip install -r requirements.txt

# 5. 后台启动新服务
echo "启动新服务..."
nohup uvicorn app:app --host 0.0.0.0 --port 8080 > chat.log 2>&1 &

# 6. 显示状态
sleep 2
if lsof -i:8080 > /dev/null 2>&1; then
    echo "✔ 服务已成功启动在 8080 端口"
    echo "查看日志: tail -f /home/chat/chat.log"
else
    echo "✘ 服务启动失败，请查看日志: cat /home/chat/chat.log"
fi