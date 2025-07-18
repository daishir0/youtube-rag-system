"""
設定管理モジュール
config.yamlファイルから設定を読み込み、システム全体で使用する設定を管理します。
"""

import yaml
import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler

@dataclass
class GeneralConfig:
    """一般設定"""
    debug: bool = False
    max_workers: int = 4
    verbosity: int = 2
    environment: str = "development"

@dataclass
class LoggingConfig:
    """ログ設定"""
    level: str = "INFO"
    file: str = "./logs/app.log"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_size_mb: int = 10
    backup_count: int = 5

@dataclass
class OpenAIConfig:
    """OpenAI API設定"""
    api_key: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 2000
    max_retries: int = 3

@dataclass
class YouTubeConfig:
    """YouTube設定"""
    subtitle_languages: List[str] = None
    subtitle_fallback_languages: List[str] = None
    sleep_interval: int = 2
    max_sleep: int = 5
    random_sleep: bool = True
    subtitle_max_retries: int = 3
    subtitle_sleep_interval: int = 5
    subtitle_429_retry_sleep: int = 30
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

@dataclass
class StorageConfig:
    """ストレージ設定"""
    transcripts_dir: str = "./data/transcripts"
    vectorstore_dir: str = "./data/vectorstore"
    processed_urls_file: str = "./data/processed_urls.json"
    metadata_dir: str = "./data/metadata"

@dataclass
class RAGConfig:
    """RAG設定"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "text-embedding-ada-002"
    retrieval_k: int = 5
    similarity_threshold: float = 0.7
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1

@dataclass
class FastAPIConfig:
    """FastAPI設定"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"
    cors_origins: List[str] = None

@dataclass
class ProxyConfig:
    """プロキシ設定"""
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 1080
    type: str = "socks5"

@dataclass
class CharacterConfig:
    """キャラクター設定"""
    name: str = "らぐちゃん"
    personality: str = "friendly"
    tone: str = "casual"
    ending_phrase: str = "～のようです"
    emoji: str = "🐾"
    greeting: str = "こんにちは！動画の内容について調べてみました"
    no_results: str = "ごめんなさい、関連する情報が見つかりませんでした"

class Config:
    """設定管理クラス"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        設定ファイルを読み込んで初期化
        
        Args:
            config_file: 設定ファイルのパス
        """
        self.config_file = config_file
        self.config_data = self._load_config()
        
        # 設定オブジェクトを作成
        self.general = self._create_general_config()
        self.logging = self._create_logging_config()
        self.openai = self._create_openai_config()
        self.youtube = self._create_youtube_config()
        self.storage = self._create_storage_config()
        self.rag = self._create_rag_config()
        self.fastapi = self._create_fastapi_config()
        self.proxy = self._create_proxy_config()
        self.character = self._create_character_config()
        
        # 必要なディレクトリを作成
        self._create_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"設定ファイル {self.config_file} が見つかりません")
            print("config.yaml.sample をコピーして config.yaml を作成してください")
            raise
        except yaml.YAMLError as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            raise
    
    def _create_general_config(self) -> GeneralConfig:
        """一般設定を作成"""
        general_data = self.config_data.get('general', {})
        return GeneralConfig(
            debug=general_data.get('debug', False),
            max_workers=general_data.get('max_workers', 4),
            verbosity=general_data.get('verbosity', 2),
            environment=general_data.get('environment', 'development')
        )
    
    def _create_logging_config(self) -> LoggingConfig:
        """ログ設定を作成"""
        logging_data = self.config_data.get('logging', {})
        return LoggingConfig(
            level=logging_data.get('level', 'INFO'),
            file=logging_data.get('file', './logs/app.log'),
            format=logging_data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            max_size_mb=logging_data.get('max_size_mb', 10),
            backup_count=logging_data.get('backup_count', 5)
        )
    
    def _create_openai_config(self) -> OpenAIConfig:
        """OpenAI設定を作成"""
        openai_data = self.config_data.get('openai', {})
        return OpenAIConfig(
            api_key=openai_data.get('api_key', ''),
            model=openai_data.get('model', 'gpt-4o-mini'),
            temperature=openai_data.get('temperature', 0.3),
            max_tokens=openai_data.get('max_tokens', 2000),
            max_retries=openai_data.get('max_retries', 3)
        )
    
    def _create_youtube_config(self) -> YouTubeConfig:
        """YouTube設定を作成"""
        youtube_data = self.config_data.get('youtube', {})
        return YouTubeConfig(
            subtitle_languages=youtube_data.get('subtitle_languages', ['ja', 'en']),
            subtitle_fallback_languages=youtube_data.get('subtitle_fallback_languages', ['ja', 'en']),
            sleep_interval=youtube_data.get('sleep_interval', 2),
            max_sleep=youtube_data.get('max_sleep', 5),
            random_sleep=youtube_data.get('random_sleep', True),
            subtitle_max_retries=youtube_data.get('subtitle_max_retries', 3),
            subtitle_sleep_interval=youtube_data.get('subtitle_sleep_interval', 5),
            subtitle_429_retry_sleep=youtube_data.get('subtitle_429_retry_sleep', 30),
            user_agent=youtube_data.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        )
    
    def _create_storage_config(self) -> StorageConfig:
        """ストレージ設定を作成"""
        storage_data = self.config_data.get('storage', {})
        return StorageConfig(
            transcripts_dir=storage_data.get('transcripts_dir', './data/transcripts'),
            vectorstore_dir=storage_data.get('vectorstore_dir', './data/vectorstore'),
            processed_urls_file=storage_data.get('processed_urls_file', './data/processed_urls.json'),
            metadata_dir=storage_data.get('metadata_dir', './data/metadata')
        )
    
    def _create_rag_config(self) -> RAGConfig:
        """RAG設定を作成"""
        rag_data = self.config_data.get('rag', {})
        return RAGConfig(
            chunk_size=rag_data.get('chunk_size', 1000),
            chunk_overlap=rag_data.get('chunk_overlap', 200),
            embedding_model=rag_data.get('embedding_model', 'text-embedding-ada-002'),
            retrieval_k=rag_data.get('retrieval_k', 5),
            similarity_threshold=rag_data.get('similarity_threshold', 0.7),
            llm_model=rag_data.get('llm_model', 'gpt-4o-mini'),
            llm_temperature=rag_data.get('llm_temperature', 0.1)
        )
    
    def _create_fastapi_config(self) -> FastAPIConfig:
        """FastAPI設定を作成"""
        fastapi_data = self.config_data.get('fastapi', {})
        return FastAPIConfig(
            host=fastapi_data.get('host', '0.0.0.0'),
            port=fastapi_data.get('port', 8000),
            reload=fastapi_data.get('reload', True),
            log_level=fastapi_data.get('log_level', 'info'),
            cors_origins=fastapi_data.get('cors_origins', ['http://localhost:3000', 'http://127.0.0.1:3000'])
        )
    
    def _create_proxy_config(self) -> ProxyConfig:
        """プロキシ設定を作成"""
        proxy_data = self.config_data.get('proxy', {})
        return ProxyConfig(
            enabled=proxy_data.get('enabled', False),
            host=proxy_data.get('host', '127.0.0.1'),
            port=proxy_data.get('port', 1080),
            type=proxy_data.get('type', 'socks5')
        )
    
    def _create_character_config(self) -> CharacterConfig:
        """キャラクター設定を作成"""
        character_data = self.config_data.get('character', {})
        return CharacterConfig(
            name=character_data.get('name', 'らぐちゃん'),
            personality=character_data.get('personality', 'friendly'),
            tone=character_data.get('tone', 'casual'),
            ending_phrase=character_data.get('ending_phrase', '～のようです'),
            emoji=character_data.get('emoji', '🐾'),
            greeting=character_data.get('greeting', 'こんにちは！動画の内容について調べてみました'),
            no_results=character_data.get('no_results', 'ごめんなさい、関連する情報が見つかりませんでした')
        )
    
    def _create_directories(self):
        """必要なディレクトリを作成"""
        directories = [
            self.storage.transcripts_dir,
            self.storage.vectorstore_dir,
            self.storage.metadata_dir,
            os.path.dirname(self.logging.file)
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self):
        """ロギングシステムを設定"""
        # ログレベルの設定
        numeric_level = getattr(logging, self.logging.level.upper(), logging.INFO)
        
        # ログフォーマットの設定
        formatter = logging.Formatter(self.logging.format)
        
        # ルートロガーの設定
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # 既存のハンドラーをクリア
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # コンソールハンドラーの設定
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # ファイルハンドラーの設定
        if self.logging.file:
            # ログファイルディレクトリの作成
            Path(self.logging.file).parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                self.logging.file,
                maxBytes=self.logging.max_size_mb * 1024 * 1024,
                backupCount=self.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # デバッグモードの場合の追加設定
        if self.general.debug:
            root_logger.setLevel(logging.DEBUG)
            console_handler.setLevel(logging.DEBUG)
            if self.logging.file:
                file_handler.setLevel(logging.DEBUG)
    
    def get_storage_path(self, path_type: str) -> Path:
        """ストレージパスを取得"""
        path_map = {
            'transcripts': self.storage.transcripts_dir,
            'vectorstore': self.storage.vectorstore_dir,
            'metadata': self.storage.metadata_dir,
            'processed_urls': self.storage.processed_urls_file
        }
        
        if path_type not in path_map:
            raise ValueError(f"不正なパスタイプ: {path_type}")
        
        return Path(path_map[path_type])
    
    def is_debug_mode(self) -> bool:
        """デバッグモードかどうかを確認"""
        return self.general.debug
    
    def print_config_summary(self):
        """設定サマリーを表示"""
        print("="*60)
        print("🔧 設定サマリー")
        print("="*60)
        print(f"📁 字幕データ: {self.storage.transcripts_dir}")
        print(f"🗄️ ベクターストア: {self.storage.vectorstore_dir}")
        print(f"🤖 OpenAI モデル: {self.openai.model}")
        print(f"🌐 FastAPI ポート: {self.fastapi.port}")
        print(f"🐛 デバッグモード: {self.general.debug}")
        print(f"📊 詳細レベル: {self.general.verbosity}")
        print("="*60)