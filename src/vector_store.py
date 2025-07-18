"""
ベクターストア管理モジュール
字幕データをベクターストアに保存・検索するためのモジュール
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document

from .config import Config

class VectorStore:
    """ベクターストア管理クラス"""
    
    def __init__(self, config: Config):
        """
        初期化
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # OpenAI APIキーは新しいクライアント形式で使用
        
        # 埋め込みモデルの初期化
        self.embeddings = OpenAIEmbeddings(
            model=self.config.rag.embedding_model,
            api_key=self.config.openai.api_key
        )
        
        # テキスト分割器の初期化
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.rag.chunk_size,
            chunk_overlap=self.config.rag.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "、", " ", ""]
        )
        
        # ベクターストアのパス
        self.vectorstore_path = self.config.get_storage_path('vectorstore')
        self.vectorstore_path.mkdir(parents=True, exist_ok=True)
        
        # メタデータファイルのパス
        self.metadata_file = self.vectorstore_path / "metadata.json"
        
        # ベクターストアオブジェクト
        self.vectorstore = None
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """
        メタデータを読み込み
        
        Returns:
            メタデータの辞書
        """
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    'created_at': datetime.now().isoformat(),
                    'last_updated': None,
                    'document_count': 0,
                    'video_count': 0,
                    'videos': {}
                }
        except Exception as e:
            self.logger.error(f"メタデータの読み込みに失敗: {e}")
            return {
                'created_at': datetime.now().isoformat(),
                'last_updated': None,
                'document_count': 0,
                'video_count': 0,
                'videos': {}
            }
    
    def _save_metadata(self):
        """メタデータを保存"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"メタデータの保存に失敗: {e}")
    
    def load(self) -> bool:
        """
        既存のベクターストアを読み込み
        
        Returns:
            読み込みに成功した場合True
        """
        try:
            faiss_index_path = self.vectorstore_path / "index.faiss"
            faiss_pkl_path = self.vectorstore_path / "index.pkl"
            
            if faiss_index_path.exists() and faiss_pkl_path.exists():
                try:
                    # 新しいバージョンでのロード
                    self.vectorstore = FAISS.load_local(
                        str(self.vectorstore_path), 
                        self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                except TypeError:
                    # 古いバージョンでのロード
                    self.vectorstore = FAISS.load_local(
                        str(self.vectorstore_path), 
                        self.embeddings
                    )
                self.logger.info("既存のベクターストアを読み込みました")
                return True
            else:
                self.logger.info("既存のベクターストアが見つかりません")
                return False
        except Exception as e:
            self.logger.error(f"ベクターストアの読み込みに失敗: {e}")
            return False
    
    def add_transcript(self, transcript_data: Dict) -> bool:
        """
        字幕データをベクターストアに追加
        
        Args:
            transcript_data: 字幕データ
            
        Returns:
            追加に成功した場合True
        """
        try:
            video_id = transcript_data['video_id']
            
            # 既に追加済みかチェック
            if video_id in self.metadata['videos']:
                self.logger.info(f"動画は既にベクターストアに追加済み: {video_id}")
                return True
            
            # 字幕テキストを結合
            transcript_text = self._combine_transcript_text(transcript_data['transcript'])
            
            if not transcript_text.strip():
                self.logger.warning(f"字幕テキストが空です: {video_id}")
                return False
            
            # テキストを分割
            documents = self._create_documents(transcript_data, transcript_text)
            
            if not documents:
                self.logger.warning(f"ドキュメントが作成できませんでした: {video_id}")
                return False
            
            # ベクターストアに追加
            if self.vectorstore is None:
                # 新規作成
                self.vectorstore = FAISS.from_documents(documents, self.embeddings)
                self.logger.info("新規ベクターストアを作成しました")
            else:
                # 既存に追加
                self.vectorstore.add_documents(documents)
                self.logger.info(f"既存ベクターストアに追加しました: {len(documents)} ドキュメント")
            
            # ベクターストアを保存
            self._save_vectorstore()
            
            # メタデータを更新
            self.metadata['videos'][video_id] = {
                'title': transcript_data['title'],
                'uploader': transcript_data['uploader'],
                'url': transcript_data['url'],
                'added_at': datetime.now().isoformat(),
                'document_count': len(documents),
                'duration': transcript_data.get('duration', 0)
            }
            self.metadata['last_updated'] = datetime.now().isoformat()
            self.metadata['document_count'] += len(documents)
            self.metadata['video_count'] = len(self.metadata['videos'])
            self._save_metadata()
            
            self.logger.info(f"字幕データをベクターストアに追加: {transcript_data['title']}")
            return True
            
        except Exception as e:
            self.logger.error(f"字幕データの追加に失敗: {e}")
            return False
    
    def _combine_transcript_text(self, transcript: List[Dict]) -> str:
        """
        字幕データをテキストに結合
        
        Args:
            transcript: 字幕データのリスト
            
        Returns:
            結合されたテキスト
        """
        if not transcript:
            return ""
        
        text_parts = []
        for entry in transcript:
            text = entry.get('text', '').strip()
            if text:
                text_parts.append(text)
        
        return ' '.join(text_parts)
    
    def _create_documents(self, transcript_data: Dict, transcript_text: str) -> List[Document]:
        """
        字幕データからドキュメントを作成
        
        Args:
            transcript_data: 字幕データ
            transcript_text: 字幕テキスト
            
        Returns:
            ドキュメントのリスト
        """
        # テキストを分割
        chunks = self.text_splitter.split_text(transcript_text)
        
        documents = []
        for i, chunk in enumerate(chunks):
            # タイムスタンプを計算（概算）
            chunk_position = i / len(chunks)
            estimated_timestamp = int(transcript_data.get('duration', 0) * chunk_position)
            
            # YouTubeのタイムスタンプURLを生成
            timestamp_url = f"{transcript_data['url']}&t={estimated_timestamp}s"
            
            metadata = {
                'video_id': transcript_data['video_id'],
                'title': transcript_data['title'],
                'uploader': transcript_data['uploader'],
                'url': transcript_data['url'],
                'timestamp_url': timestamp_url,
                'timestamp': estimated_timestamp,
                'chunk_id': i,
                'total_chunks': len(chunks),
                'upload_date': transcript_data.get('upload_date', ''),
                'duration': transcript_data.get('duration', 0),
                'view_count': transcript_data.get('view_count', 0),
                'channel_id': transcript_data.get('channel_id', ''),
                'channel_url': transcript_data.get('channel_url', ''),
            }
            
            documents.append(Document(
                page_content=chunk,
                metadata=metadata
            ))
        
        return documents
    
    def _save_vectorstore(self):
        """ベクターストアを保存"""
        try:
            if self.vectorstore:
                self.vectorstore.save_local(str(self.vectorstore_path))
                self.logger.debug("ベクターストアを保存しました")
        except Exception as e:
            self.logger.error(f"ベクターストアの保存に失敗: {e}")
    
    def search(self, query: str, k: int = None) -> List[Dict]:
        """
        ベクターストアで検索
        
        Args:
            query: 検索クエリ
            k: 取得する結果数
            
        Returns:
            検索結果のリスト
        """
        if not self.vectorstore:
            self.logger.warning("ベクターストアが読み込まれていません")
            return []
        
        if k is None:
            k = self.config.rag.retrieval_k
        
        try:
            # 類似度検索
            docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)
            
            results = []
            for doc, score in docs_with_scores:
                # 類似度スコアを0-1の範囲に正規化（FAISSの距離は小さいほど類似）
                similarity_score = 1 / (1 + score)
                
                # 閾値チェック
                if similarity_score < self.config.rag.similarity_threshold:
                    continue
                
                result = {
                    'content': doc.page_content,
                    'score': similarity_score,
                    'video_id': doc.metadata['video_id'],
                    'title': doc.metadata['title'],
                    'uploader': doc.metadata['uploader'],
                    'url': doc.metadata['url'],
                    'timestamp_url': doc.metadata['timestamp_url'],
                    'timestamp': doc.metadata['timestamp'],
                    'chunk_id': doc.metadata['chunk_id'],
                    'upload_date': doc.metadata.get('upload_date', ''),
                    'duration': doc.metadata.get('duration', 0),
                    'view_count': doc.metadata.get('view_count', 0),
                }
                results.append(result)
            
            # スコアの高い順にソート
            results.sort(key=lambda x: x['score'], reverse=True)
            
            self.logger.info(f"検索完了: {len(results)} 件の結果")
            return results
            
        except Exception as e:
            self.logger.error(f"検索に失敗: {e}")
            return []
    
    def update_from_file(self, file_path: Path) -> bool:
        """
        更新されたファイルからベクターストアを更新
        
        Args:
            file_path: 更新されたファイルのパス
            
        Returns:
            更新に成功した場合True
        """
        try:
            # ファイルから字幕データを読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
            
            video_id = transcript_data['video_id']
            
            # 既存のドキュメントを削除（FAISSでは難しいので再構築）
            if video_id in self.metadata['videos']:
                self.logger.info(f"動画の更新のため再構築が必要: {video_id}")
                # 実際の実装では、FAISSの制限により完全な再構築が必要
                # ここでは簡易的に追加のみ実装
                return self.add_transcript(transcript_data)
            else:
                return self.add_transcript(transcript_data)
            
        except Exception as e:
            self.logger.error(f"ファイルからの更新に失敗: {file_path} - {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        ベクターストアの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        return {
            'video_count': self.metadata['video_count'],
            'document_count': self.metadata['document_count'],
            'last_updated': self.metadata['last_updated'],
            'created_at': self.metadata['created_at'],
            'videos': list(self.metadata['videos'].keys())
        }
    
    def remove_video(self, video_id: str) -> bool:
        """
        動画をベクターストアから削除
        
        Args:
            video_id: 削除する動画のID
            
        Returns:
            削除に成功した場合True
        """
        # FAISSでは個別のドキュメント削除が困難
        # 実装が必要な場合は、全体を再構築する必要がある
        self.logger.warning("FAISSでは個別削除は困難です。再構築が必要です。")
        return False
    
    def rebuild_from_transcripts(self, transcripts_dir: Path) -> bool:
        """
        字幕ディレクトリからベクターストアを再構築
        
        Args:
            transcripts_dir: 字幕ディレクトリ
            
        Returns:
            再構築に成功した場合True
        """
        try:
            self.logger.info("ベクターストアの再構築を開始")
            
            # 既存のベクターストアとメタデータをクリア
            self.vectorstore = None
            self.metadata = {
                'created_at': datetime.now().isoformat(),
                'last_updated': None,
                'document_count': 0,
                'video_count': 0,
                'videos': {}
            }
            
            # 字幕ファイルを読み込んで追加
            transcript_files = list(transcripts_dir.glob("*.json"))
            success_count = 0
            
            for file_path in transcript_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        transcript_data = json.load(f)
                    
                    if self.add_transcript(transcript_data):
                        success_count += 1
                        self.logger.info(f"再構築: {transcript_data['title']}")
                    
                except Exception as e:
                    self.logger.error(f"ファイル処理エラー: {file_path} - {e}")
                    continue
            
            self.logger.info(f"ベクターストアの再構築完了: {success_count}/{len(transcript_files)} 件")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"ベクターストアの再構築に失敗: {e}")
            return False
    
    def print_statistics(self):
        """統計情報を表示"""
        stats = self.get_statistics()
        print("="*50)
        print("🗄️ ベクターストア統計")
        print("="*50)
        print(f"🎬 動画数: {stats['video_count']} 件")
        print(f"📄 ドキュメント数: {stats['document_count']} 件")
        print(f"🕒 最終更新: {stats['last_updated'] or 'なし'}")
        print(f"📅 作成日: {stats['created_at']}")
        print("="*50)