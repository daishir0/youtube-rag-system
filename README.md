# youtube-rag-system

## Overview
YouTube RAG System is an intelligent video content analysis and Q&A system that downloads YouTube video subtitles, processes them using AI embeddings, and provides interactive question-answering capabilities. The system features a FastAPI backend with vector search capabilities and a modern Next.js frontend for seamless user interaction.

Key features:
- **Automatic subtitle extraction** from YouTube videos using yt-dlp
- **AI-powered vector search** with OpenAI embeddings and FAISS
- **Interactive Q&A interface** with character-based responses
- **Real-time web interface** built with Next.js and Tailwind CSS
- **RESTful API** for integration with other applications
- **Multi-language support** (Japanese and English subtitles)

## Installation

### Prerequisites
- Python 3.11+ with conda environment
- Node.js 18+ and npm
- OpenAI API key
- Git

### Step-by-step Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/daishir0/youtube-rag-system
   cd youtube-rag-system
   ```

2. **Set up the environment**
   ```bash
   # Run the setup script
   ./setup_env.sh setup
   ```

3. **Configure environment settings**
   ```bash
   # Edit environment configuration (set your conda environment name)
   nano env_config.sh
   ```

4. **Configure API settings**
   ```bash
   # Edit configuration file and add your OpenAI API key
   nano config.yaml
   ```
   Update the `openai.api_key` field with your actual API key.

5. **Install dependencies**
   ```bash
   # Python dependencies (in your conda environment)
   conda activate your-env-name
   pip install -r requirements.txt
   
   # Frontend dependencies
   cd frontend
   npm install
   cd ..
   ```

## Usage

### Starting the System
```bash
# Start both backend and frontend
./server.sh start

# Check system status
./server.sh status

# Stop the system
./server.sh stop
```

### Command Line Interface
```bash
# Add YouTube videos to the system
python main.py https://www.youtube.com/watch?v=VIDEO_ID

# Interactive Q&A mode
python main.py

# Start API server only
python main.py --server

# Rebuild vector store
python main.py --rebuild
```

### Web Interface
After starting the system, access the web interface at:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### API Endpoints
- `POST /videos/add` - Add YouTube videos
- `POST /question` - Ask questions about video content
- `POST /search` - Search video content
- `GET /status` - System status
- `GET /videos/similar` - Find similar videos

## Notes
- Ensure your OpenAI API key is properly configured before use
- The system stores processed video data in the `data/` directory
- Vector embeddings are cached for improved performance
- Subtitle extraction supports multiple languages (Japanese and English by default)
- The character-based response system provides friendly AI interactions
- All logs are stored in the `logs/` directory for troubleshooting

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# youtube-rag-system

## 概要
YouTube RAG システムは、YouTube動画の字幕を自動取得し、AIによる埋め込み処理を行い、インタラクティブな質問応答機能を提供するインテリジェントな動画コンテンツ分析システムです。FastAPIによるバックエンドとモダンなNext.jsフロントエンドを組み合わせたシステムです。

主な機能:
- **YouTube動画の字幕自動取得** - yt-dlpを使用した高性能字幕抽出
- **AIベクター検索** - OpenAI埋め込みとFAISSによる高精度検索
- **インタラクティブQ&A** - キャラクターベースの親しみやすい応答
- **リアルタイムWebインターフェース** - Next.jsとTailwind CSSによる現代的UI
- **RESTful API** - 他アプリケーションとの統合に対応
- **多言語対応** - 日本語・英語字幕のサポート

## インストール方法

### 前提条件
- Python 3.11+ （conda環境）
- Node.js 18+ と npm
- OpenAI APIキー
- Git

### Step by stepのインストール方法

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/daishir0/youtube-rag-system
   cd youtube-rag-system
   ```

2. **環境セットアップ**
   ```bash
   # セットアップスクリプトの実行
   ./setup_env.sh setup
   ```

3. **環境設定の編集**
   ```bash
   # 環境設定ファイルの編集（conda環境名を設定）
   nano env_config.sh
   ```

4. **API設定の編集**
   ```bash
   # 設定ファイルの編集（OpenAI APIキーを追加）
   nano config.yaml
   ```
   `openai.api_key` フィールドに実際のAPIキーを設定してください。

5. **依存関係のインストール**
   ```bash
   # Python依存関係（conda環境内で）
   conda activate your-env-name
   pip install -r requirements.txt
   
   # フロントエンド依存関係
   cd frontend
   npm install
   cd ..
   ```

## 使い方

### システムの起動
```bash
# バックエンドとフロントエンドの両方を起動
./server.sh start

# システム状態の確認
./server.sh status

# システムの停止
./server.sh stop
```

### コマンドラインインターフェース
```bash
# YouTube動画をシステムに追加
python main.py https://www.youtube.com/watch?v=VIDEO_ID

# 対話型Q&Aモード
python main.py

# APIサーバーのみ起動
python main.py --server

# ベクターストアの再構築
python main.py --rebuild
```

### Webインターフェース
システム起動後、以下のURLでアクセスできます：
- フロントエンド: http://localhost:3001
- バックエンドAPI: http://localhost:8000
- API文書: http://localhost:8000/docs

### APIエンドポイント
- `POST /videos/add` - YouTube動画の追加
- `POST /question` - 動画内容に関する質問
- `POST /search` - 動画コンテンツの検索
- `GET /status` - システム状態の取得
- `GET /videos/similar` - 類似動画の検索

## 注意点
- 使用前にOpenAI APIキーが適切に設定されていることを確認してください
- 処理済み動画データは `data/` ディレクトリに保存されます
- ベクター埋め込みはパフォーマンス向上のためキャッシュされます
- 字幕抽出は複数言語（デフォルトで日本語・英語）をサポートします
- キャラクターベースの応答システムにより親しみやすいAI対話が実現されます
- すべてのログは `logs/` ディレクトリに保存され、トラブルシューティングに使用できます

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。