"""
RAGシステム（検索・質問応答）モジュール
ベクターストアを使用した検索と、LLMによる質問応答を提供
"""

import logging
from typing import List, Dict, Optional
import openai
from datetime import datetime

from .config import Config
from .vector_store import VectorStore

class RAGSystem:
    """RAGシステムクラス"""
    
    def __init__(self, config: Config):
        """
        初期化
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.vector_store = VectorStore(config)
        
        # OpenAI APIキーは新しいクライアント形式で使用
        
        # システムプロンプトの設定（キャラクター設定を反映）
        self.system_prompt = f"""あなたは「{self.config.character.name}」というキャラクターで、YouTube動画の内容に基づいて質問に答えるAIアシスタントです。

【キャラクター設定】
- 名前: {self.config.character.name}
- 性格: {self.config.character.personality}
- 口調: {self.config.character.tone}
- 語尾: {self.config.character.ending_phrase}

以下のガイドラインに従って回答してください：

1. 提供されたYouTube動画の字幕データのみを使用して回答してください
2. 回答は日本語で、わかりやすく親しみやすい口調で答えてください
3. 文章の終わりには「{self.config.character.ending_phrase}」を付けてください
4. 引用した内容がある場合は、該当する動画のタイトルと時間を明記してください
5. 複数の動画から情報を得た場合は、それぞれの動画の情報を整理して答えてください
6. 質問に対する答えが字幕データにない場合は、正直に「提供された動画の内容からは回答できません{self.config.character.ending_phrase}」と答えてください
7. 動画のURLとタイムスタンプも可能な限り提供してください

字幕データの情報：
- 動画タイトル
- 投稿者名
- 動画URL（タイムスタンプ付き）
- 字幕内容
- 再生時間

親しみやすく、優しい口調で回答してください。
"""
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        質問に対してRAG検索を実行
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
            
        Returns:
            検索結果のリスト
        """
        try:
            # ベクターストアを読み込み
            if not self.vector_store.load():
                self.logger.error("ベクターストアの読み込みに失敗")
                return []
            
            # ベクターストアで検索
            search_results = self.vector_store.search(query, k=max_results)
            
            if not search_results:
                self.logger.info("検索結果が見つかりませんでした")
                return []
            
            # 結果を整形
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    'title': result['title'],
                    'uploader': result['uploader'],
                    'url': result['timestamp_url'],
                    'content': result['content'],
                    'score': result['score'],
                    'timestamp': self._format_timestamp(result['timestamp']),
                    'video_id': result['video_id'],
                    'chunk_id': result['chunk_id']
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"検索中にエラーが発生: {e}")
            return []
    
    def answer_question(self, question: str, max_results: int = 5) -> Dict:
        """
        質問に対してLLMを使用して回答を生成
        
        Args:
            question: 質問
            max_results: 検索結果の最大数
            
        Returns:
            回答データの辞書
        """
        try:
            # 関連する動画を検索
            search_results = self.search(question, max_results)
            
            if not search_results:
                return {
                    'answer': '申し訳ありませんが、ご質問に関連する動画の内容が見つかりませんでした。',
                    'sources': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            # コンテキストを構築
            context = self._build_context(search_results)
            
            # LLMで回答を生成
            answer = self._generate_answer(question, context)
            
            # ソース情報を整理
            sources = self._format_sources(search_results)
            
            return {
                'answer': answer,
                'sources': sources,
                'timestamp': datetime.now().isoformat(),
                'context_used': len(search_results)
            }
            
        except Exception as e:
            self.logger.error(f"質問応答中にエラーが発生: {e}")
            return {
                'answer': 'エラーが発生しました。もう一度お試しください。',
                'sources': [],
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _build_context(self, search_results: List[Dict]) -> str:
        """
        検索結果からコンテキストを構築
        
        Args:
            search_results: 検索結果のリスト
            
        Returns:
            構築されたコンテキスト
        """
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            context_part = f"""
【動画 {i}】
タイトル: {result['title']}
投稿者: {result['uploader']}
URL: {result['url']}
時間: {result['timestamp']}
内容: {result['content']}
関連度: {result['score']:.1%}

"""
            context_parts.append(context_part)
        
        return '\n'.join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """
        LLMを使用して回答を生成
        
        Args:
            question: 質問
            context: コンテキスト
            
        Returns:
            生成された回答
        """
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"""
以下の YouTube 動画の字幕データを参考に、質問に答えてください。

質問: {question}

参考データ:
{context}

回答:"""}
            ]
            
            client = openai.OpenAI(api_key=self.config.openai.api_key)
            response = client.chat.completions.create(
                model=self.config.rag.llm_model,
                messages=messages,
                temperature=self.config.rag.llm_temperature,
                max_tokens=self.config.openai.max_tokens,
                timeout=30
            )
            
            answer = response.choices[0].message.content.strip()
            
            return answer
            
        except Exception as e:
            self.logger.error(f"LLMでの回答生成に失敗: {e}")
            return f"回答の生成中にエラーが発生しました: {str(e)}"
    
    def _format_sources(self, search_results: List[Dict]) -> List[Dict]:
        """
        ソース情報を整形
        
        Args:
            search_results: 検索結果のリスト
            
        Returns:
            整形されたソース情報のリスト
        """
        sources = []
        seen_chunks = set()
        
        for result in search_results:
            chunk_id = result['chunk_id']
            
            # 同じチャンクの重複を避けるため、チャンクIDで重複チェック
            if chunk_id not in seen_chunks:
                source = {
                    'title': result['title'],
                    'uploader': result['uploader'],
                    'url': result['url'],
                    'timestamp': result['timestamp'],
                    'score': result['score'],
                    'content': result['content'],
                    'video_id': result['video_id'],
                    'chunk_id': chunk_id
                }
                sources.append(source)
                seen_chunks.add(chunk_id)
        
        return sources
    
    def _format_timestamp(self, seconds: int) -> str:
        """
        秒数を時間形式に変換
        
        Args:
            seconds: 秒数
            
        Returns:
            時間形式の文字列
        """
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours}時間{minutes}分{seconds}秒"
    
    def get_similar_videos(self, query: str, limit: int = 10) -> List[Dict]:
        """
        類似動画を検索
        
        Args:
            query: 検索クエリ
            limit: 結果数の上限
            
        Returns:
            類似動画のリスト
        """
        try:
            # ベクターストアを読み込み
            if not self.vector_store.load():
                return []
            
            # 検索実行
            search_results = self.vector_store.search(query, k=limit)
            
            # 動画単位で結果を集約
            video_scores = {}
            for result in search_results:
                video_id = result['video_id']
                if video_id not in video_scores:
                    video_scores[video_id] = {
                        'title': result['title'],
                        'uploader': result['uploader'],
                        'url': result['url'],
                        'video_id': video_id,
                        'max_score': result['score'],
                        'avg_score': result['score'],
                        'chunk_count': 1
                    }
                else:
                    video_scores[video_id]['max_score'] = max(
                        video_scores[video_id]['max_score'], 
                        result['score']
                    )
                    video_scores[video_id]['avg_score'] = (
                        video_scores[video_id]['avg_score'] * video_scores[video_id]['chunk_count'] + 
                        result['score']
                    ) / (video_scores[video_id]['chunk_count'] + 1)
                    video_scores[video_id]['chunk_count'] += 1
            
            # スコアでソート
            similar_videos = sorted(
                video_scores.values(),
                key=lambda x: x['max_score'],
                reverse=True
            )
            
            return similar_videos[:limit]
            
        except Exception as e:
            self.logger.error(f"類似動画検索中にエラーが発生: {e}")
            return []
    
    def get_video_summary(self, video_id: str) -> Optional[Dict]:
        """
        動画の要約を生成
        
        Args:
            video_id: 動画ID
            
        Returns:
            動画の要約データ
        """
        try:
            # ベクターストアを読み込み
            if not self.vector_store.load():
                return None
            
            # 動画IDで検索
            search_results = self.vector_store.search(f"video_id:{video_id}", k=50)
            
            if not search_results:
                return None
            
            # 動画の全内容を結合
            all_content = []
            video_info = None
            
            for result in search_results:
                if result['video_id'] == video_id:
                    all_content.append(result['content'])
                    if video_info is None:
                        video_info = {
                            'title': result['title'],
                            'uploader': result['uploader'],
                            'url': result['url'],
                            'video_id': video_id
                        }
            
            if not all_content or not video_info:
                return None
            
            # 要約を生成
            full_content = ' '.join(all_content)
            summary = self._generate_summary(full_content, video_info)
            
            return {
                'video_id': video_id,
                'title': video_info['title'],
                'uploader': video_info['uploader'],
                'url': video_info['url'],
                'summary': summary,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"動画要約生成中にエラーが発生: {e}")
            return None
    
    def _generate_summary(self, content: str, video_info: Dict) -> str:
        """
        動画の要約を生成
        
        Args:
            content: 動画の全内容
            video_info: 動画情報
            
        Returns:
            生成された要約
        """
        try:
            messages = [
                {"role": "system", "content": """あなたは動画の内容を要約するAIアシスタントです。
以下のガイドラインに従って要約してください：

1. 動画の主要なポイントを3-5個の箇条書きで整理
2. 重要なキーワードや概念を含める
3. 簡潔で理解しやすい日本語で記述
4. 動画の長さに応じて適切な詳細レベルを選択"""},
                {"role": "user", "content": f"""
以下のYouTube動画の字幕内容を要約してください。

動画タイトル: {video_info['title']}
投稿者: {video_info['uploader']}

字幕内容:
{content[:4000]}  # トークン制限を考慮して切り詰め

要約:"""}
            ]
            
            response = openai.ChatCompletion.create(
                model=self.config.rag.llm_model,
                messages=messages,
                temperature=0.3,  # 要約では一貫性を重視
                max_tokens=self.config.openai.max_tokens // 2,
                timeout=30
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            self.logger.error(f"要約生成に失敗: {e}")
            return f"要約生成中にエラーが発生しました: {str(e)}"