#!/bin/bash

# YouTube RAG System - Server Control Script
# バックエンド(FastAPI)とフロントエンド(Next.js)の管理スクリプト

# 設定ファイルの読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_CONFIG="$SCRIPT_DIR/env_config.sh"

if [ -f "$ENV_CONFIG" ]; then
    source "$ENV_CONFIG"
else
    echo "Error: env_config.sh not found. Please copy env_config.sh.sample to env_config.sh and configure it."
    exit 1
fi

# ログディレクトリを作成
mkdir -p "$LOG_DIR"

# 色付きメッセージ用関数
print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

# プロセスが動作中かチェック
is_backend_running() {
    if [ -f "$BACKEND_PID_FILE" ]; then
        local pid=$(cat "$BACKEND_PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            return 0
        else
            rm -f "$BACKEND_PID_FILE"
            return 1
        fi
    fi
    return 1
}

is_frontend_running() {
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            return 0
        else
            rm -f "$FRONTEND_PID_FILE"
            return 1
        fi
    fi
    return 1
}

# バックエンドの起動
start_backend() {
    print_info "バックエンドを起動中..."
    
    if is_backend_running; then
        print_warning "バックエンドは既に起動中です"
        return 0
    fi
    
    cd "$BACKEND_DIR"
    
    # conda環境でバックエンドを起動
    nohup bash -c "
        source ~/.bashrc
        conda activate $CONDA_ENV
        python -c \"
import uvicorn
from src.config import Config
from src.rag_system import RAGSystem
from src.api_server import create_app

config = Config()
rag_system = RAGSystem(config)
app = create_app(config, rag_system)
uvicorn.run(app, host='0.0.0.0', port=$BACKEND_PORT, reload=False)
        \"
    " > "$BACKEND_LOG" 2>&1 &
    
    local backend_pid=$!
    echo $backend_pid > "$BACKEND_PID_FILE"
    
    # 起動確認
    sleep 5
    if is_backend_running; then
        print_success "バックエンドが起動しました (PID: $backend_pid, Port: $BACKEND_PORT)"
        print_info "ログファイル: $BACKEND_LOG"
    else
        print_error "バックエンドの起動に失敗しました"
        return 1
    fi
}

# フロントエンドの起動
start_frontend() {
    print_info "フロントエンドを起動中..."
    
    if is_frontend_running; then
        print_warning "フロントエンドは既に起動中です"
        return 0
    fi
    
    cd "$FRONTEND_DIR"
    
    # フロントエンドを起動
    nohup npm run dev -- --port $FRONTEND_PORT > "$FRONTEND_LOG" 2>&1 &
    
    local frontend_pid=$!
    echo $frontend_pid > "$FRONTEND_PID_FILE"
    
    # 起動確認
    sleep 5
    if is_frontend_running; then
        print_success "フロントエンドが起動しました (PID: $frontend_pid, Port: $FRONTEND_PORT)"
        print_info "ログファイル: $FRONTEND_LOG"
    else
        print_error "フロントエンドの起動に失敗しました"
        return 1
    fi
}

# バックエンドの停止
stop_backend() {
    print_info "バックエンドを停止中..."
    
    if ! is_backend_running; then
        print_warning "バックエンドは起動していません"
        return 0
    fi
    
    local pid=$(cat "$BACKEND_PID_FILE")
    kill $pid 2>/dev/null
    
    # 強制終了が必要な場合
    sleep 3
    if ps -p $pid > /dev/null 2>&1; then
        print_warning "強制終了中..."
        kill -9 $pid 2>/dev/null
    fi
    
    rm -f "$BACKEND_PID_FILE"
    print_success "バックエンドを停止しました"
}

# フロントエンドの停止
stop_frontend() {
    print_info "フロントエンドを停止中..."
    
    if ! is_frontend_running; then
        print_warning "フロントエンドは起動していません"
        return 0
    fi
    
    local pid=$(cat "$FRONTEND_PID_FILE")
    kill $pid 2>/dev/null
    
    # 強制終了が必要な場合
    sleep 3
    if ps -p $pid > /dev/null 2>&1; then
        print_warning "強制終了中..."
        kill -9 $pid 2>/dev/null
    fi
    
    rm -f "$FRONTEND_PID_FILE"
    print_success "フロントエンドを停止しました"
}

# ステータス確認
show_status() {
    echo "=================================="
    echo "YouTube RAG System - Server Status"
    echo "=================================="
    
    echo -n "バックエンド (Port $BACKEND_PORT): "
    if is_backend_running; then
        local pid=$(cat "$BACKEND_PID_FILE")
        echo -e "\033[32m起動中\033[0m (PID: $pid)"
    else
        echo -e "\033[31m停止中\033[0m"
    fi
    
    echo -n "フロントエンド (Port $FRONTEND_PORT): "
    if is_frontend_running; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        echo -e "\033[32m起動中\033[0m (PID: $pid)"
    else
        echo -e "\033[31m停止中\033[0m"
    fi
    
    echo ""
    echo "アクセスURL:"
    echo "  バックエンド: http://localhost:$BACKEND_PORT"
    echo "  フロントエンド: http://localhost:$FRONTEND_PORT"
    echo "  API文書: http://localhost:$BACKEND_PORT/docs"
}

# ログの表示
show_logs() {
    local service=$1
    case $service in
        backend)
            print_info "バックエンドログを表示中..."
            tail -f "$BACKEND_LOG"
            ;;
        frontend)
            print_info "フロントエンドログを表示中..."
            tail -f "$FRONTEND_LOG"
            ;;
        *)
            print_error "不正なサービス名: $service"
            echo "使用方法: $0 logs [backend|frontend]"
            exit 1
            ;;
    esac
}

# ヘルプメッセージ
show_help() {
    echo "YouTube RAG System - Server Control Script"
    echo ""
    echo "使用方法: $0 [コマンド] [オプション]"
    echo ""
    echo "コマンド:"
    echo "  start [backend|frontend|all]  - サーバーを起動"
    echo "  stop [backend|frontend|all]   - サーバーを停止"
    echo "  restart [backend|frontend|all] - サーバーを再起動"
    echo "  status                         - サーバーの状態を確認"
    echo "  logs [backend|frontend]        - ログを表示"
    echo "  help                           - このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 start all      # 両方のサーバーを起動"
    echo "  $0 stop backend   # バックエンドのみ停止"
    echo "  $0 restart frontend # フロントエンドのみ再起動"
    echo "  $0 status         # 状態確認"
    echo "  $0 logs backend   # バックエンドのログを表示"
}

# メイン処理
main() {
    case $1 in
        start)
            case $2 in
                backend)
                    start_backend
                    ;;
                frontend)
                    start_frontend
                    ;;
                all|"")
                    start_backend
                    start_frontend
                    ;;
                *)
                    print_error "不正なオプション: $2"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        stop)
            case $2 in
                backend)
                    stop_backend
                    ;;
                frontend)
                    stop_frontend
                    ;;
                all|"")
                    stop_frontend
                    stop_backend
                    ;;
                *)
                    print_error "不正なオプション: $2"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        restart)
            case $2 in
                backend)
                    stop_backend
                    sleep 2
                    start_backend
                    ;;
                frontend)
                    stop_frontend
                    sleep 2
                    start_frontend
                    ;;
                all|"")
                    stop_frontend
                    stop_backend
                    sleep 2
                    start_backend
                    start_frontend
                    ;;
                *)
                    print_error "不正なオプション: $2"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs $2
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "不正なコマンド: $1"
            show_help
            exit 1
            ;;
    esac
}

# 引数がない場合はヘルプを表示
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# メイン処理を実行
main "$@"