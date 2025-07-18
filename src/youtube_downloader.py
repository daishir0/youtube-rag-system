"""
YouTube動画から字幕をダウンロードするモジュール
"""

import re
import time
import logging
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import random

import yt_dlp
from urllib.parse import urlparse, parse_qs

from .config import Config

class YouTubeDownloader:
    """YouTube動画から字幕をダウンロードするクラス"""
    
    def __init__(self, config: Config):
        """
        初期化
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # yt-dlpの設定
        self.ydl_opts = {
            'extract_flat': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'quiet': not self.config.general.debug,
            'no_warnings': not self.config.general.debug,
            'user_agent': self.config.youtube.user_agent,
        }
        
        # プロキシ設定
        if self.config.proxy.enabled:
            self.ydl_opts['proxy'] = f"{self.config.proxy.type}://{self.config.proxy.host}:{self.config.proxy.port}"
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        YouTubeのURLから動画IDを抽出
        
        Args:
            url: YouTube動画のURL
            
        Returns:
            動画ID、抽出できない場合はNone
        """
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
            r'(?:v/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be/)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        動画の基本情報を取得
        
        Args:
            url: YouTube動画のURL
            
        Returns:
            動画情報の辞書、取得できない場合はNone
        """
        # より安全な設定を使用
        safe_ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['dash', 'hls']
                }
            }
        }
        
        # プロキシ設定
        if self.config.proxy.enabled:
            safe_ydl_opts['proxy'] = f"{self.config.proxy.type}://{self.config.proxy.host}:{self.config.proxy.port}"
        
        try:
            with yt_dlp.YoutubeDL(safe_ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'duration': info.get('duration'),
                    'description': info.get('description'),
                    'view_count': info.get('view_count'),
                    'url': url,
                    'thumbnail': info.get('thumbnail'),
                    'channel_id': info.get('channel_id'),
                    'channel_url': info.get('channel_url'),
                }
        except Exception as e:
            self.logger.error(f"動画情報の取得に失敗: {url} - {e}")
            return None
    
    def download_transcript(self, url: str) -> Optional[Dict]:
        """
        YouTube動画から字幕をダウンロード
        
        Args:
            url: YouTube動画のURL
            
        Returns:
            字幕データの辞書、取得できない場合はNone
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            self.logger.error(f"動画IDの抽出に失敗: {url}")
            return None
        
        self.logger.info(f"字幕ダウンロード開始: {video_id}")
        
        # 動画情報を取得
        video_info = self.get_video_info(url)
        if not video_info:
            self.logger.error(f"動画情報の取得に失敗: {url}")
            return None
        
        # 字幕を取得
        transcript_text = self._get_transcript_text(video_id)
        if not transcript_text:
            self.logger.error(f"字幕の取得に失敗: {video_id}")
            return None
        
        # 字幕データを作成
        transcript_data = {
            'video_id': video_id,
            'title': video_info['title'],
            'uploader': video_info['uploader'],
            'upload_date': video_info['upload_date'],
            'duration': video_info['duration'],
            'description': video_info.get('description', ''),
            'view_count': video_info.get('view_count', 0),
            'url': url,
            'thumbnail': video_info.get('thumbnail'),
            'channel_id': video_info.get('channel_id'),
            'channel_url': video_info.get('channel_url'),
            'transcript': transcript_text,
            'download_date': datetime.now().isoformat(),
        }
        
        # ファイルに保存
        self._save_transcript_to_file(transcript_data)
        
        self.logger.info(f"字幕ダウンロード完了: {video_info['title']}")
        return transcript_data
    
    def _get_transcript_text(self, video_id: str) -> Optional[List[Dict]]:
        """
        yt-dlpを使用して字幕を取得
        
        Args:
            video_id: YouTube動画ID
            
        Returns:
            字幕のリスト、取得できない場合はNone
        """
        for attempt in range(self.config.youtube.subtitle_max_retries):
            try:
                # 一時的な作業ディレクトリを作成
                temp_dir = self.config.get_storage_path('transcripts') / 'temp'
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                # 字幕をダウンロード
                transcript_data = self._download_subtitle_with_yt_dlp(video_id, temp_dir)
                if transcript_data:
                    return transcript_data
                
                self.logger.warning(f"字幕が見つかりません: {video_id}")
                return None
                    
            except Exception as e:
                self.logger.warning(f"字幕取得の試行 {attempt + 1} 失敗: {video_id} - {e}")
                if attempt < self.config.youtube.subtitle_max_retries - 1:
                    sleep_time = self.config.youtube.subtitle_sleep_interval * (attempt + 1)
                    if "429" in str(e):
                        sleep_time = self.config.youtube.subtitle_429_retry_sleep
                    
                    self.logger.info(f"{sleep_time}秒待機後にリトライ")
                    time.sleep(sleep_time)
                else:
                    self.logger.error(f"字幕取得の最大試行回数に達しました: {video_id}")
                    return None
        
        return None
    
    def _save_transcript_to_file(self, transcript_data: Dict):
        """
        字幕データをファイルに保存
        
        Args:
            transcript_data: 字幕データ
        """
        try:
            # ファイル名を作成（動画IDベース）
            filename = f"{transcript_data['video_id']}.json"
            filepath = self.config.get_storage_path('transcripts') / filename
            
            # ディレクトリが存在しない場合は作成
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # ファイルに保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"字幕ファイルを保存: {filepath}")
            
        except Exception as e:
            self.logger.error(f"字幕ファイルの保存に失敗: {e}")
    
    def load_transcript_from_file(self, video_id: str) -> Optional[Dict]:
        """
        ファイルから字幕データを読み込み
        
        Args:
            video_id: YouTube動画ID
            
        Returns:
            字幕データ、ファイルが存在しない場合はNone
        """
        try:
            filename = f"{video_id}.json"
            filepath = self.config.get_storage_path('transcripts') / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"字幕ファイルの読み込みに失敗: {video_id} - {e}")
            return None
    
    def get_transcript_file_path(self, video_id: str) -> Path:
        """
        字幕ファイルのパスを取得
        
        Args:
            video_id: YouTube動画ID
            
        Returns:
            字幕ファイルのパス
        """
        filename = f"{video_id}.json"
        return self.config.get_storage_path('transcripts') / filename
    
    def _download_subtitle_with_yt_dlp(self, video_id: str, temp_dir: Path) -> Optional[List[Dict]]:
        """
        yt-dlpを使用して字幕をダウンロード (refsの実装を参考)
        
        Args:
            video_id: YouTube動画ID
            temp_dir: 一時ディレクトリ
            
        Returns:
            字幕データのリスト、取得できない場合はNone
        """
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # refsの実装を参考した言語フォールバック戦略
        fallback_languages = self.config.youtube.subtitle_fallback_languages or ['ja', 'en']
        
        # 各言語で試行
        for lang in fallback_languages:
            self.logger.debug(f"Attempting to download subtitles in language: {lang}")
            
            # 言語間で少し待機
            if lang != fallback_languages[0]:
                time.sleep(self.config.youtube.subtitle_sleep_interval)
            
            result = self._download_subtitle_for_language(video_url, temp_dir, lang)
            if result:
                self.logger.info(f"Successfully downloaded subtitles in language: {lang}")
                return result
        
        self.logger.warning(f"No subtitles found for {video_url} in any fallback language")
        return None
    
    def _download_subtitle_for_language(self, video_url: str, temp_dir: Path, language: str) -> Optional[List[Dict]]:
        """
        特定の言語で字幕をダウンロード (refsの実装を参考)
        
        Args:
            video_url: YouTube動画URL
            temp_dir: 一時ディレクトリ
            language: 字幕の言語
            
        Returns:
            字幕データのリスト、取得できない場合はNone
        """
        # refsの実装と完全に同じ設定を使用（シンプルに保つ）
        ydl_opts = {
            'writeautomaticsub': True,  # 自動字幕のみ
            'subtitleslangs': [language],  # 単一言語のみ
            'skip_download': True,
            'outtmpl': str(temp_dir / 'subtitle.%(ext)s'),  # シンプルなファイル名
            'subtitlesformat': 'vtt',  # VTTでタイムスタンプを保持
            'quiet': True,
        }
        
        # プロキシ設定
        if self.config.proxy.enabled:
            ydl_opts['proxy'] = f"{self.config.proxy.type}://{self.config.proxy.host}:{self.config.proxy.port}"
        
        # 429エラーのリトライ機構
        for attempt in range(self.config.youtube.subtitle_max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    
                    # ダウンロードされた字幕ファイルを探す
                    for pattern in [f"subtitle.{language}.vtt", f"subtitle.{language}-auto.vtt"]:
                        subtitle_path = temp_dir / pattern
                        if subtitle_path.exists():
                            # VTTファイルを処理
                            transcript_data = self._process_vtt_file(subtitle_path)
                            # 一時ファイルを削除
                            self._cleanup_temp_files(temp_dir)
                            return transcript_data
                    
                    # ファイルが見つからない場合、この言語は利用できない
                    self.logger.debug(f"No subtitles available for language: {language}")
                    return None
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                # 429エラーの特別処理
                if '429' in error_msg or 'too many requests' in error_msg:
                    if attempt < self.config.youtube.subtitle_max_retries - 1:
                        wait_time = self.config.youtube.subtitle_429_retry_sleep * (attempt + 1)
                        self.logger.warning(f"429 error for subtitles in {language}, waiting {wait_time} seconds (attempt {attempt + 1}/{self.config.youtube.subtitle_max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"429 error persists for subtitles in {language} after {self.config.youtube.subtitle_max_retries} attempts")
                        return None
                # Bad RequestやPreconditionエラーの処理
                elif '400' in error_msg or 'bad request' in error_msg or 'precondition' in error_msg:
                    self.logger.warning(f"YouTube API error for {language}: {e}")
                    return None
                else:
                    # その他のエラー - ログして次の言語を試す
                    self.logger.debug(f"Failed to download subtitles for {language}: {e}")
                    return None
        
        return None
    
    def _process_vtt_file(self, vtt_file: Path) -> List[Dict]:
        """
        VTTファイルを処理して字幕データを抽出
        
        Args:
            vtt_file: VTTファイルのパス
            
        Returns:
            字幕データのリスト
        """
        transcript_data = []
        
        try:
            with open(vtt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_segment = None
            
            for line in lines:
                line = line.strip()
                
                # VTTヘッダーと空行をスキップ
                if (not line or line.startswith('WEBVTT') or 
                    line.startswith('NOTE') or line.startswith('Kind:') or 
                    line.startswith('Language:')):
                    continue
                
                # タイムスタンプ行 (例: "00:01:30.500 --> 00:01:33.200")
                if '-->' in line:
                    if current_segment:
                        transcript_data.append(current_segment)
                    
                    # タイムスタンプを解析
                    times = line.split(' --> ')
                    start_time = self._parse_vtt_timestamp(times[0])
                    end_time = self._parse_vtt_timestamp(times[1])
                    
                    current_segment = {
                        'start': start_time,
                        'duration': end_time - start_time,
                        'text': ''
                    }
                
                # テキスト行
                elif current_segment is not None and not re.match(r'^\d+$', line):
                    # VTTフォーマットタグを削除
                    clean_text = re.sub(r'<[^>]*>', '', line)
                    if clean_text.strip():
                        if current_segment['text']:
                            current_segment['text'] += ' '
                        current_segment['text'] += clean_text.strip()
            
            # 最後のセグメントを追加
            if current_segment:
                transcript_data.append(current_segment)
            
            return transcript_data
            
        except Exception as e:
            self.logger.error(f"VTTファイルの処理に失敗: {vtt_file} - {e}")
            return []
    
    def _parse_vtt_timestamp(self, timestamp: str) -> float:
        """
        VTTのタイムスタンプを秒に変換
        
        Args:
            timestamp: VTTタイムスタンプ (例: "00:01:30.500")
            
        Returns:
            秒数
        """
        try:
            # HH:MM:SS.mmm または MM:SS.mmm 形式
            parts = timestamp.strip().split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return int(minutes) * 60 + float(seconds)
            else:
                return float(parts[0])
        except Exception:
            return 0.0
    
    def _cleanup_temp_files(self, temp_dir: Path):
        """
        一時ファイルを削除
        
        Args:
            temp_dir: 一時ディレクトリ
        """
        try:
            for file in temp_dir.glob('*'):
                if file.is_file():
                    file.unlink()
        except Exception as e:
            self.logger.warning(f"一時ファイルの削除に失敗: {e}")
    
    def _add_random_delay(self):
        """ランダムな遅延を追加"""
        if self.config.youtube.random_sleep:
            sleep_time = random.uniform(
                self.config.youtube.sleep_interval,
                self.config.youtube.max_sleep
            )
            time.sleep(sleep_time)