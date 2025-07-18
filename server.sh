#!/bin/bash

# YouTube RAG System - 簡単操作用スクリプト
# server_control.shのラッパー

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTROL_SCRIPT="$SCRIPT_DIR/server_control.sh"

# 設定ファイルの読み込み
ENV_CONFIG="$SCRIPT_DIR/env_config.sh"
if [ -f "$ENV_CONFIG" ]; then
    source "$ENV_CONFIG"
else
    echo "Warning: env_config.sh not found. Using default values."
    BACKEND_PORT=8000
    FRONTEND_PORT=3001
fi

# 色付きメッセージ
print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

# 現在動作中のサーバーを停止
stop_current_servers() {
    print_info "現在動作中のサーバーを停止中..."
    
    # 現在動作中のpythonプロセス(API server)を停止
    pkill -f "python.*uvicorn" 2>/dev/null
    pkill -f "python.*api_server" 2>/dev/null
    
    # 現在動作中のnodeプロセス(frontend)を停止
    pkill -f "node.*next" 2>/dev/null
    pkill -f "npm.*dev" 2>/dev/null
    
    # ポートを使用しているプロセスを停止
    local backend_pid=$(lsof -ti:$BACKEND_PORT 2>/dev/null)
    local frontend_pid=$(lsof -ti:$FRONTEND_PORT 2>/dev/null)
    
    if [ -n "$backend_pid" ]; then
        kill -9 $backend_pid 2>/dev/null
        print_info "バックエンドプロセス (PID: $backend_pid) を停止しました"
    fi
    
    if [ -n "$frontend_pid" ]; then
        kill -9 $frontend_pid 2>/dev/null
        print_info "フロントエンドプロセス (PID: $frontend_pid) を停止しました"
    fi
    
    # PIDファイルをクリア
    rm -f /tmp/youtube_rag_*.pid
    
    sleep 2
    print_success "既存のサーバーを停止しました"
}

case $1 in
    start)
        print_info "YouTube RAG Systemを起動中..."
        stop_current_servers
        "$CONTROL_SCRIPT" start all
        ;;
    stop)
        print_info "YouTube RAG Systemを停止中..."
        stop_current_servers
        "$CONTROL_SCRIPT" stop all
        ;;
    restart)
        print_info "YouTube RAG Systemを再起動中..."
        stop_current_servers
        "$CONTROL_SCRIPT" start all
        ;;
    status)
        "$CONTROL_SCRIPT" status
        ;;
    logs)
        "$CONTROL_SCRIPT" logs $2
        ;;
    *)
        echo "YouTube RAG System - 簡単操作"
        echo ""
        echo "使用方法: $0 [コマンド]"
        echo ""
        echo "コマンド:"
        echo "  start    - システム全体を起動"
        echo "  stop     - システム全体を停止"
        echo "  restart  - システム全体を再起動"
        echo "  status   - システムの状態確認"
        echo "  logs     - ログを表示"
        echo ""
        echo "詳細操作: $CONTROL_SCRIPT help"
        ;;
esac