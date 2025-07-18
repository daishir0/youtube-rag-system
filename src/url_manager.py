"""
処理済みURL管理モジュール
YouTube動画URLの処理状況を管理し、重複処理を防ぐ
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import os

from .config import Config

class URLManager:
    """処理済みURL管理クラス"""
    
    def __init__(self, config: Config):
        """
        初期化
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processed_urls_file = self.config.get_storage_path('processed_urls')
        self.processed_urls = self._load_processed_urls()
    
    def _load_processed_urls(self) -> Dict[str, Dict]:
        """
        処理済みURLリストを読み込み
        
        Returns:
            処理済みURLの辞書
        """
        try:
            if self.processed_urls_file.exists():
                with open(self.processed_urls_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"処理済みURL {len(data)} 件を読み込みました")
                    return data
            else:
                self.logger.info("処理済みURLファイルが存在しません。新規作成します")
                return {}
        except Exception as e:
            self.logger.error(f"処理済みURLファイルの読み込みに失敗: {e}")
            return {}
    
    def _save_processed_urls(self):
        """処理済みURLリストを保存"""
        try:
            # ディレクトリが存在しない場合は作成
            self.processed_urls_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.processed_urls_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_urls, f, ensure_ascii=False, indent=2)
            
            self.logger.debug("処理済みURLファイルを保存しました")
            
        except Exception as e:
            self.logger.error(f"処理済みURLファイルの保存に失敗: {e}")
    
    def is_processed(self, url: str) -> bool:
        """
        URLが処理済みかチェック
        
        Args:
            url: チェックするURL
            
        Returns:
            処理済みの場合True
        """
        return url in self.processed_urls
    
    def mark_processed(self, url: str, video_data: Dict):
        """
        URLを処理済みとしてマーク
        
        Args:
            url: 処理済みとしてマークするURL
            video_data: 動画データ
        """
        self.processed_urls[url] = {
            'video_id': video_data.get('video_id'),
            'title': video_data.get('title'),
            'uploader': video_data.get('uploader'),
            'processed_date': datetime.now().isoformat(),
            'file_path': str(self.config.get_storage_path('transcripts') / f"{video_data.get('video_id')}.json"),
            'vectorstore_added': False,  # ベクターストアに追加されたかのフラグ
            'last_modified': datetime.now().isoformat()
        }
        self._save_processed_urls()
        self.logger.info(f"URLを処理済みとしてマーク: {url}")
    
    def mark_vectorstore_added(self, url: str):
        """
        URLのベクターストア追加フラグを更新
        
        Args:
            url: 更新するURL
        """
        if url in self.processed_urls:
            self.processed_urls[url]['vectorstore_added'] = True
            self.processed_urls[url]['last_modified'] = datetime.now().isoformat()
            self._save_processed_urls()
            self.logger.info(f"ベクターストア追加フラグを更新: {url}")
    
    def get_processed_urls(self) -> Dict[str, Dict]:
        """
        処理済みURLの辞書を取得
        
        Returns:
            処理済みURLの辞書
        """
        return self.processed_urls.copy()
    
    def get_processed_count(self) -> int:
        """
        処理済みURL数を取得
        
        Returns:
            処理済みURL数
        """
        return len(self.processed_urls)
    
    def get_unprocessed_for_vectorstore(self) -> List[str]:
        """
        ベクターストアに未追加のURLリストを取得
        
        Returns:
            ベクターストアに未追加のURLリスト
        """
        unprocessed = []
        for url, data in self.processed_urls.items():
            if not data.get('vectorstore_added', False):
                unprocessed.append(url)
        return unprocessed
    
    def remove_processed_url(self, url: str):
        """
        処理済みURLを削除
        
        Args:
            url: 削除するURL
        """
        if url in self.processed_urls:
            del self.processed_urls[url]
            self._save_processed_urls()
            self.logger.info(f"処理済みURLを削除: {url}")
    
    def find_updated_transcripts(self) -> List[Path]:
        """
        更新された字幕ファイルを検索
        
        Returns:
            更新された字幕ファイルのパスリスト
        """
        updated_files = []
        transcripts_dir = self.config.get_storage_path('transcripts')
        
        if not transcripts_dir.exists():
            return updated_files
        
        for url, data in self.processed_urls.items():
            video_id = data.get('video_id')
            if not video_id:
                continue
            
            transcript_file = transcripts_dir / f"{video_id}.json"
            if not transcript_file.exists():
                continue
            
            # ファイルの更新日時を取得
            file_modified_time = datetime.fromtimestamp(transcript_file.stat().st_mtime)
            
            # 処理済みデータの最終更新日時を取得
            last_modified_str = data.get('last_modified', data.get('processed_date'))
            if last_modified_str:
                try:
                    last_modified = datetime.fromisoformat(last_modified_str)
                    
                    # ファイルの方が新しい場合は更新されたファイルとして追加
                    if file_modified_time > last_modified:
                        updated_files.append(transcript_file)
                        self.logger.info(f"更新されたファイル検出: {transcript_file}")
                except ValueError:
                    # 日時のパースに失敗した場合はスキップ
                    continue
        
        return updated_files
    
    def update_file_timestamp(self, video_id: str):
        """
        ファイルのタイムスタンプを更新
        
        Args:
            video_id: 動画ID
        """
        # 該当するURLを検索
        for url, data in self.processed_urls.items():
            if data.get('video_id') == video_id:
                data['last_modified'] = datetime.now().isoformat()
                self._save_processed_urls()
                self.logger.info(f"ファイルタイムスタンプを更新: {video_id}")
                break
    
    def get_video_data_by_id(self, video_id: str) -> Optional[Dict]:
        """
        動画IDから動画データを取得
        
        Args:
            video_id: 動画ID
            
        Returns:
            動画データ、見つからない場合はNone
        """
        for url, data in self.processed_urls.items():
            if data.get('video_id') == video_id:
                return {
                    'url': url,
                    **data
                }
        return None
    
    def get_statistics(self) -> Dict:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        total_count = len(self.processed_urls)
        vectorstore_added_count = sum(1 for data in self.processed_urls.values() 
                                     if data.get('vectorstore_added', False))
        
        return {
            'total_processed': total_count,
            'vectorstore_added': vectorstore_added_count,
            'vectorstore_pending': total_count - vectorstore_added_count,
            'updated_files': len(self.find_updated_transcripts())
        }
    
    def print_statistics(self):
        """統計情報を表示"""
        stats = self.get_statistics()
        print("="*50)
        print("📊 URL管理統計")
        print("="*50)
        print(f"📺 処理済み動画: {stats['total_processed']} 件")
        print(f"🏗️ ベクターストア追加済み: {stats['vectorstore_added']} 件")
        print(f"⏳ ベクターストア未追加: {stats['vectorstore_pending']} 件")
        print(f"🔄 更新されたファイル: {stats['updated_files']} 件")
        print("="*50)
    
    def cleanup_missing_files(self):
        """
        存在しないファイルの処理済みURLを削除
        """
        transcripts_dir = self.config.get_storage_path('transcripts')
        urls_to_remove = []
        
        for url, data in self.processed_urls.items():
            video_id = data.get('video_id')
            if video_id:
                transcript_file = transcripts_dir / f"{video_id}.json"
                if not transcript_file.exists():
                    urls_to_remove.append(url)
        
        for url in urls_to_remove:
            self.remove_processed_url(url)
            self.logger.info(f"存在しないファイルの処理済みURLを削除: {url}")
        
        if urls_to_remove:
            self.logger.info(f"クリーンアップ完了: {len(urls_to_remove)} 件の処理済みURLを削除")
        else:
            self.logger.info("クリーンアップ: 削除対象なし")