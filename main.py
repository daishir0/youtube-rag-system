#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube RAG System
シンプルなYouTube動画字幕ダウンロード・RAGシステム
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import asyncio
import uvicorn

# 環境変数設定
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 現在のディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.youtube_downloader import YouTubeDownloader
from src.vector_store import VectorStore
from src.rag_system import RAGSystem
from src.url_manager import URLManager
from src.api_server import create_app

class YouTubeRAGSystem:
    """YouTube RAG システムのメインクラス"""
    
    def __init__(self):
        """初期化"""
        try:
            self.config = Config()
            self.config.setup_logging()
            self.logger = logging.getLogger(__name__)
            
            # コンポーネント初期化
            self.downloader = YouTubeDownloader(self.config)
            self.vector_store = VectorStore(self.config)
            self.rag_system = RAGSystem(self.config)
            self.url_manager = URLManager(self.config)
            
            self.logger.info("YouTube RAG システムが正常に初期化されました")
            
        except Exception as e:
            print(f"初期化に失敗しました: {e}")
            sys.exit(1)
    
    def process_videos(self, video_urls: List[str]):
        """動画URLリストを処理"""
        print("="*60)
        print("🎯 YouTube RAG システム - 動画処理モード")
        print("="*60)
        print(f"📺 処理する動画数: {len(video_urls)}")
        
        success_count = 0
        failed_count = 0
        
        for i, url in enumerate(video_urls, 1):
            print(f"\n🔄 動画 {i}/{len(video_urls)} を処理中: {url}")
            print("-" * 50)
            
            try:
                # 処理済みかチェック
                if self.url_manager.is_processed(url):
                    print(f"⏭️  既に処理済み: {url}")
                    continue
                
                # 字幕ダウンロード
                print("📥 字幕をダウンロード中...")
                transcript_data = self.downloader.download_transcript(url)
                
                if not transcript_data:
                    print(f"❌ 字幕の取得に失敗: {url}")
                    failed_count += 1
                    continue
                
                # ベクターストアに保存
                print("🏗️ ベクターストアに保存中...")
                if self.vector_store.add_transcript(transcript_data):
                    print(f"✅ 処理完了: {transcript_data['title']}")
                    self.url_manager.mark_processed(url, transcript_data)
                    success_count += 1
                else:
                    print(f"❌ ベクターストアへの保存に失敗: {url}")
                    failed_count += 1
                
            except Exception as e:
                print(f"❌ 処理中にエラーが発生: {url} - {e}")
                self.logger.error(f"動画処理エラー: {url} - {e}")
                failed_count += 1
        
        # 結果サマリー
        print("\n" + "="*60)
        print("📊 処理結果サマリー")
        print("="*60)
        print(f"✅ 成功: {success_count} 動画")
        print(f"❌ 失敗: {failed_count} 動画")
        print(f"📈 成功率: {(success_count / len(video_urls)) * 100:.1f}%")
        
        if success_count > 0:
            print("\n🎉 処理が完了しました!")
            print("🔍 質問応答モードで検索できます")
    
    def start_interactive_mode(self):
        """対話型質問応答モード"""
        print("="*60)
        print("🔍 YouTube RAG システム - 質問応答モード")
        print("="*60)
        
        # ベクターストアの初期化
        if not self.vector_store.load():
            print("❌ ベクターストアが見つかりません")
            print("💡 まず動画URLを指定してデータを追加してください")
            return
        
        print("✅ ベクターストアが読み込まれました")
        print("💡 質問を入力してください（'quit'で終了）")
        print("-" * 60)
        
        while True:
            try:
                query = input("\n🤔 質問: ").strip()
                
                if not query or query.lower() in ['quit', 'exit', 'q']:
                    print("👋 質問応答モードを終了します")
                    break
                
                print("🔍 検索中...")
                answer_data = self.rag_system.answer_question(query)
                
                if answer_data['sources']:
                    # AI回答を表示
                    print(f"\n{self.config.character.emoji} {self.config.character.greeting}")
                    print("="*60)
                    print(f"📝 回答: {answer_data['answer']}")
                    print("="*60)
                    
                    # 検索結果の詳細を表示
                    print(f"✅ {len(answer_data['sources'])} 件の関連する結果が見つかりました:")
                    print("="*60)
                    
                    for i, result in enumerate(answer_data['sources'], 1):
                        print(f"{i}. 📹 {result['title']}")
                        print(f"   👤 {result['uploader']}")
                        print(f"   🔗 {result['url']}")
                        print(f"   📊 関連度: {result['score']:.1%}")
                        print(f"   📝 内容: {result['content'][:200]}...")
                        if result.get('timestamp'):
                            print(f"   ⏰ タイムスタンプ: {result['timestamp']}")
                        print()
                else:
                    print(f"❌ {self.config.character.no_results}")
                    print("💡 別のキーワードで試してください")
                    
            except KeyboardInterrupt:
                print("\n👋 質問応答モードを終了します")
                break
            except Exception as e:
                print(f"❌ 検索中にエラーが発生: {e}")
                self.logger.error(f"検索エラー: {e}")
    
    def rebuild_vectorstore(self):
        """ベクターストアを再構築"""
        print("="*60)
        print("🔄 ベクターストア再構築モード")
        print("="*60)
        
        print("🔍 更新されたファイルを検索中...")
        updated_files = self.url_manager.find_updated_transcripts()
        
        if not updated_files:
            print("✅ 更新されたファイルはありません")
            return
        
        print(f"📁 {len(updated_files)} 個の更新されたファイルが見つかりました")
        
        for file_path in updated_files:
            print(f"🔄 更新中: {file_path}")
            try:
                # ファイルを再読み込みしてベクターストアを更新
                if self.vector_store.update_from_file(file_path):
                    print(f"✅ 更新完了: {file_path}")
                else:
                    print(f"❌ 更新失敗: {file_path}")
            except Exception as e:
                print(f"❌ 更新エラー: {file_path} - {e}")
                self.logger.error(f"ファイル更新エラー: {file_path} - {e}")
        
        print("\n🎉 ベクターストアの再構築が完了しました")
    
    def start_api_server(self):
        """FastAPIサーバーを起動"""
        print("="*60)
        print("🚀 FastAPI サーバーを起動中...")
        print("="*60)
        
        app = create_app(self.config, self.rag_system)
        
        uvicorn.run(
            app,
            host=self.config.fastapi.host,
            port=self.config.fastapi.port,
            reload=self.config.fastapi.reload,
            log_level=self.config.fastapi.log_level
        )

def show_help():
    """ヘルプメッセージを表示"""
    help_text = """
🎯 YouTube RAG システム - 使用方法

基本的な使用方法:
  python main.py [動画URL1] [動画URL2] ...    動画の字幕をダウンロードしてRAGシステムに追加
  python main.py                             質問応答モードで検索
  python main.py --rebuild                   ベクターストアを再構築
  python main.py --server                    FastAPIサーバーを起動
  python main.py --help                      このヘルプを表示

オプション:
  --rebuild     字幕ファイルが更新された場合にベクターストアを再構築
  --server      FastAPIサーバーを起動（フロントエンド用）
  --help        このヘルプメッセージを表示

使用例:
  # 動画を追加
  python main.py https://www.youtube.com/watch?v=VIDEO_ID1 https://www.youtube.com/watch?v=VIDEO_ID2
  
  # 質問応答モード
  python main.py
  
  # ベクターストア再構築
  python main.py --rebuild
  
  # APIサーバー起動
  python main.py --server

注意事項:
  - 初回実行前にconfig.yamlでOpenAI APIキーを設定してください
  - 既に処理済みの動画URLは自動的にスキップされます
  - 字幕ファイルを手動で修正した場合は --rebuild オプションを使用してください
"""
    print(help_text)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='YouTube RAG システム',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('urls', nargs='*', help='処理するYouTube動画のURL')
    parser.add_argument('--rebuild', action='store_true', help='ベクターストアを再構築')
    parser.add_argument('--server', action='store_true', help='FastAPIサーバーを起動')
    parser.add_argument('--help-detail', action='store_true', help='詳細なヘルプを表示')
    
    args = parser.parse_args()
    
    if args.help_detail:
        show_help()
        return
    
    try:
        system = YouTubeRAGSystem()
        
        if args.server:
            # APIサーバーモード
            system.start_api_server()
        elif args.rebuild:
            # 再構築モード
            system.rebuild_vectorstore()
        elif args.urls:
            # 動画処理モード
            system.process_videos(args.urls)
        else:
            # 質問応答モード
            system.start_interactive_mode()
            
    except KeyboardInterrupt:
        print("\n🛑 操作がキャンセルされました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()