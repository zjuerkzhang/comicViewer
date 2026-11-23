
#!/bin/bash

REMOTE_USER="kzhang"
REMOTE_HOST="192.168.119.26"

LOCAL_PORT=9222
REMOTE_PORT=9222

PID_FILE="/tmp/cdp-tunnel.pid"
LOG_FILE="/tmp/cdp-tunnel.log"

start() {
    # 检查是否已经运行
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "CDP tunnel is already running."
        return
    fi

    # 建立 SSH 隧道
    ssh -f -N \
        -L 127.0.0.1:${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT} \
        -o ExitOnForwardFailure=yes \
        -o ServerAliveInterval=30 \
        -o ServerAliveCountMax=3 \
        ${REMOTE_USER}@${REMOTE_HOST} \
        -E "$LOG_FILE"

    if [ $? -eq 0 ]; then
        # 记录 SSH 进程 PID
        pgrep -f "ssh.*127.0.0.1:${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" \
            | head -n 1 > "$PID_FILE"

        echo "CDP tunnel started."
        echo "Local endpoint: http://127.0.0.1:${LOCAL_PORT}"
    else
        echo "Failed to start CDP tunnel."
        return 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null
        rm -f "$PID_FILE"
        echo "CDP tunnel stopped."
    else
        echo "CDP tunnel is not running."
    fi
}

status() {
    if curl -fsS http://127.0.0.1:${LOCAL_PORT}/json/version >/dev/null; then
        echo "CDP tunnel is available."
        curl -fsS http://127.0.0.1:${LOCAL_PORT}/json/version
    else
        echo "CDP tunnel is unavailable."
    fi
}

case "$1" in
    start)  start ;;
    stop)   stop ;;
    status) status ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
