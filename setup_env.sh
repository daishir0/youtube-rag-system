#!/bin/bash

# YouTube RAG System - Environment Setup Script
# 環境設定用スクリプト

# 設定ファイルの読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_CONFIG="$SCRIPT_DIR/env_config.sh"

if [ -f "$ENV_CONFIG" ]; then
    source "$ENV_CONFIG"
else
    # 初回セットアップの場合はサンプルファイルから作成
    if [ -f "$SCRIPT_DIR/env_config.sh.sample" ]; then
        echo "Creating env_config.sh from sample..."
        cp "$SCRIPT_DIR/env_config.sh.sample" "$ENV_CONFIG"
        source "$ENV_CONFIG"
    else
        echo "Error: env_config.sh.sample not found."
        exit 1
    fi
fi

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

# 設定ファイルのセットアップ
setup_config() {
    print_info "設定ファイルのセットアップを開始します..."
    
    # バックエンド設定
    if [ ! -f "config.yaml" ]; then
        if [ -f "config.yaml.sample" ]; then
            cp config.yaml.sample config.yaml
            print_success "config.yaml を作成しました"
            print_warning "config.yaml でOpenAI APIキーを設定してください"
        else
            print_error "config.yaml.sample が見つかりません"
            return 1
        fi
    else
        print_info "config.yaml は既に存在します"
    fi
    
    # フロントエンド設定
    if [ ! -f "frontend/.env.local" ]; then
        if [ -f "frontend/.env.local.sample" ]; then
            cp frontend/.env.local.sample frontend/.env.local
            print_success "frontend/.env.local を作成しました"
        else
            print_info "frontend/.env.local.sample が見つかりません（オプション）"
        fi
    else
        print_info "frontend/.env.local は既に存在します"
    fi
}

# 必要なディレクトリの作成
setup_directories() {
    print_info "必要なディレクトリを作成中..."
    
    # データディレクトリ
    mkdir -p data/transcripts
    mkdir -p data/vectorstore
    mkdir -p data/metadata
    mkdir -p logs
    
    print_success "ディレクトリを作成しました"
}

# 依存関係のインストール（Python）
install_python_deps() {
    print_info "Python依存関係のインストールを確認中..."
    
    if [ -f "requirements.txt" ]; then
        print_info "conda環境 $CONDA_ENV で依存関係をインストールします..."
        conda activate "$CONDA_ENV"
        pip install -r requirements.txt
        print_success "Python依存関係のインストールが完了しました"
    else
        print_error "requirements.txt が見つかりません"
        return 1
    fi
}

# 依存関係のインストール（Node.js）
install_node_deps() {
    print_info "Node.js依存関係のインストールを確認中..."
    
    if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
        cd frontend
        print_info "npm依存関係をインストールします..."
        npm install
        cd ..
        print_success "Node.js依存関係のインストールが完了しました"
    else
        print_error "frontend/package.json が見つかりません"
        return 1
    fi
}

# 設定確認
check_config() {
    print_info "設定を確認中..."
    
    # OpenAI APIキーの確認
    if grep -q "your-openai-api-key-here" config.yaml 2>/dev/null; then
        print_error "OpenAI APIキーが設定されていません"
        print_info "config.yaml を編集してAPIキーを設定してください"
        return 1
    fi
    
    print_success "設定確認が完了しました"
}

# ヘルプメッセージ
show_help() {
    echo "YouTube RAG System - Environment Setup Script"
    echo ""
    echo "使用方法: $0 [コマンド]"
    echo ""
    echo "コマンド:"
    echo "  setup     - 完全セットアップ（推奨）"
    echo "  config    - 設定ファイルのセットアップのみ"
    echo "  dirs      - ディレクトリ作成のみ"
    echo "  python    - Python依存関係インストールのみ"
    echo "  node      - Node.js依存関係インストールのみ"
    echo "  check     - 設定確認のみ"
    echo "  help      - このヘルプを表示"
    echo ""
    echo "セットアップ後の作業:"
    echo "  1. config.yaml でOpenAI APIキーを設定"
    echo "  2. ./server.sh start でシステムを起動"
}

# メイン処理
main() {
    case $1 in
        setup)
            setup_config
            setup_directories
            install_python_deps
            install_node_deps
            check_config
            ;;
        config)
            setup_config
            ;;
        dirs)
            setup_directories
            ;;
        python)
            install_python_deps
            ;;
        node)
            install_node_deps
            ;;
        check)
            check_config
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            if [ -z "$1" ]; then
                show_help
            else
                print_error "不正なコマンド: $1"
                show_help
                exit 1
            fi
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