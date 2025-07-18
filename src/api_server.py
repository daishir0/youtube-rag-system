"""
FastAPI バックエンドサーバー
YouTube RAG システムのWeb API
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import uvicorn

from .config import Config
from .rag_system import RAGSystem
from .youtube_downloader import YouTubeDownloader
from .vector_store import VectorStore
from .url_manager import URLManager

# リクエスト・レスポンスモデル
class VideoURLRequest(BaseModel):
    """動画URL追加リクエスト"""
    urls: List[HttpUrl]

class SearchRequest(BaseModel):
    """検索リクエスト"""
    query: str
    max_results: int = 5

class QuestionRequest(BaseModel):
    """質問リクエスト"""
    question: str
    max_results: int = 5

class VideoProcessResponse(BaseModel):
    """動画処理レスポンス"""
    message: str
    processed_count: int
    failed_count: int
    results: List[Dict]

class SearchResponse(BaseModel):
    """検索レスポンス"""
    query: str
    results: List[Dict]
    total_results: int
    timestamp: str

class AnswerResponse(BaseModel):
    """回答レスポンス"""
    question: str
    answer: str
    sources: List[Dict]
    timestamp: str
    context_used: int

class StatusResponse(BaseModel):
    """システム状態レスポンス"""
    status: str
    video_count: int
    document_count: int
    processed_urls: int
    last_updated: Optional[str]

# 依存性注入
def get_rag_system():
    """RAGシステムインスタンスを取得"""
    return current_app.state.rag_system

def get_config():
    """設定インスタンスを取得"""
    return current_app.state.config

def get_downloader():
    """ダウンローダーインスタンスを取得"""
    return current_app.state.downloader

def get_vector_store():
    """ベクターストアインスタンスを取得"""
    return current_app.state.vector_store

def get_url_manager():
    """URL管理インスタンスを取得"""
    return current_app.state.url_manager

# グローバル変数
current_app = None

def create_app(config: Config, rag_system: RAGSystem) -> FastAPI:
    """
    FastAPIアプリケーションを作成
    
    Args:
        config: 設定オブジェクト
        rag_system: RAGシステム
        
    Returns:
        FastAPIアプリケーション
    """
    global current_app
    
    app = FastAPI(
        title="YouTube RAG API",
        description="YouTube動画の字幕を使用したRAG（Retrieval-Augmented Generation）システム",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.fastapi.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 状態管理
    app.state.config = config
    app.state.rag_system = rag_system
    app.state.downloader = YouTubeDownloader(config)
    app.state.vector_store = VectorStore(config)
    app.state.url_manager = URLManager(config)
    
    current_app = app
    
    # ロガーの設定
    logger = logging.getLogger(__name__)
    
    @app.on_event("startup")
    async def startup_event():
        """アプリケーション起動時の処理"""
        logger.info("YouTube RAG API サーバーが起動しました")
        
        # ベクターストアの初期化
        if not app.state.vector_store.load():
            logger.info("既存のベクターストアが見つかりません")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """アプリケーション終了時の処理"""
        logger.info("YouTube RAG API サーバーが終了しました")
    
    # ルート定義
    
    @app.get("/", response_model=Dict)
    async def root():
        """ルートエンドポイント"""
        return {
            "message": "YouTube RAG API Server",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "running"
        }
    
    @app.get("/health")
    async def health_check():
        """ヘルスチェック"""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    @app.get("/status", response_model=StatusResponse)
    async def get_status():
        """システム状態を取得"""
        try:
            vector_stats = app.state.vector_store.get_statistics()
            url_stats = app.state.url_manager.get_statistics()
            
            return StatusResponse(
                status="active",
                video_count=vector_stats["video_count"],
                document_count=vector_stats["document_count"],
                processed_urls=url_stats["total_processed"],
                last_updated=vector_stats["last_updated"]
            )
        except Exception as e:
            logger.error(f"状態取得エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/videos/add", response_model=VideoProcessResponse)
    async def add_videos(
        request: VideoURLRequest,
        background_tasks: BackgroundTasks
    ):
        """動画URLを追加（バックグラウンド処理）"""
        try:
            urls = [str(url) for url in request.urls]
            
            # バックグラウンドタスクとして処理
            background_tasks.add_task(process_videos_task, urls)
            
            return VideoProcessResponse(
                message=f"{len(urls)} 個の動画の処理を開始しました",
                processed_count=0,
                failed_count=0,
                results=[]
            )
        except Exception as e:
            logger.error(f"動画追加エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/videos/add-sync", response_model=VideoProcessResponse)
    async def add_videos_sync(request: VideoURLRequest):
        """動画URLを追加（同期処理）"""
        try:
            urls = [str(url) for url in request.urls]
            result = await process_videos_sync(urls)
            return result
        except Exception as e:
            logger.error(f"同期動画追加エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/search", response_model=SearchResponse)
    async def search_videos(request: SearchRequest):
        """動画を検索"""
        try:
            results = app.state.rag_system.search(
                request.query, 
                request.max_results
            )
            
            return SearchResponse(
                query=request.query,
                results=results,
                total_results=len(results),
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"検索エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/question", response_model=AnswerResponse)
    async def ask_question(request: QuestionRequest):
        """質問に回答"""
        try:
            response = app.state.rag_system.answer_question(
                request.question,
                request.max_results
            )
            
            return AnswerResponse(
                question=request.question,
                answer=response["answer"],
                sources=response["sources"],
                timestamp=response["timestamp"],
                context_used=response.get("context_used", 0)
            )
        except Exception as e:
            logger.error(f"質問応答エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/videos/similar")
    async def get_similar_videos(
        query: str = Query(..., description="検索クエリ"),
        limit: int = Query(10, description="結果数の上限")
    ):
        """類似動画を取得"""
        try:
            results = app.state.rag_system.get_similar_videos(query, limit)
            
            return {
                "query": query,
                "similar_videos": results,
                "total_results": len(results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"類似動画取得エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/videos/{video_id}/summary")
    async def get_video_summary(video_id: str):
        """動画の要約を取得"""
        try:
            summary = app.state.rag_system.get_video_summary(video_id)
            
            if not summary:
                raise HTTPException(status_code=404, detail="動画が見つかりません")
            
            return summary
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"動画要約取得エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/rebuild")
    async def rebuild_vectorstore(background_tasks: BackgroundTasks):
        """ベクターストアを再構築"""
        try:
            background_tasks.add_task(rebuild_task)
            
            return {
                "message": "ベクターストアの再構築を開始しました",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"再構築エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/videos/processed")
    async def get_processed_videos():
        """処理済み動画のリストを取得"""
        try:
            processed_urls = app.state.url_manager.get_processed_urls()
            
            return {
                "processed_videos": processed_urls,
                "total_count": len(processed_urls),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"処理済み動画取得エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/videos/{video_id}")
    async def delete_video(video_id: str):
        """動画を削除"""
        try:
            # URL管理から削除
            video_data = app.state.url_manager.get_video_data_by_id(video_id)
            if not video_data:
                raise HTTPException(status_code=404, detail="動画が見つかりません")
            
            # ファイルを削除
            transcript_file = app.state.downloader.get_transcript_file_path(video_id)
            if transcript_file.exists():
                transcript_file.unlink()
            
            # URL管理から削除
            app.state.url_manager.remove_processed_url(video_data["url"])
            
            return {
                "message": f"動画 {video_id} を削除しました",
                "timestamp": datetime.now().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"動画削除エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # バックグラウンドタスク
    
    async def process_videos_task(urls: List[str]):
        """動画処理タスク（バックグラウンド）"""
        logger.info(f"動画処理開始: {len(urls)} 個")
        
        success_count = 0
        failed_count = 0
        
        for url in urls:
            try:
                # 処理済みかチェック
                if app.state.url_manager.is_processed(url):
                    logger.info(f"既に処理済み: {url}")
                    continue
                
                # 字幕ダウンロード
                transcript_data = app.state.downloader.download_transcript(url)
                if not transcript_data:
                    failed_count += 1
                    continue
                
                # ベクターストアに追加
                if app.state.vector_store.add_transcript(transcript_data):
                    app.state.url_manager.mark_processed(url, transcript_data)
                    app.state.url_manager.mark_vectorstore_added(url)
                    success_count += 1
                else:
                    failed_count += 1
                
            except Exception as e:
                logger.error(f"動画処理エラー: {url} - {e}")
                failed_count += 1
        
        logger.info(f"動画処理完了: 成功 {success_count}, 失敗 {failed_count}")
    
    async def process_videos_sync(urls: List[str]) -> VideoProcessResponse:
        """動画処理（同期）"""
        success_count = 0
        failed_count = 0
        results = []
        
        for url in urls:
            try:
                # 処理済みかチェック
                if app.state.url_manager.is_processed(url):
                    results.append({
                        "url": url,
                        "status": "skipped",
                        "message": "既に処理済み"
                    })
                    continue
                
                # 字幕ダウンロード
                transcript_data = app.state.downloader.download_transcript(url)
                if not transcript_data:
                    failed_count += 1
                    results.append({
                        "url": url,
                        "status": "failed",
                        "message": "字幕の取得に失敗"
                    })
                    continue
                
                # ベクターストアに追加
                if app.state.vector_store.add_transcript(transcript_data):
                    app.state.url_manager.mark_processed(url, transcript_data)
                    app.state.url_manager.mark_vectorstore_added(url)
                    success_count += 1
                    results.append({
                        "url": url,
                        "status": "success",
                        "message": "処理完了",
                        "title": transcript_data["title"]
                    })
                else:
                    failed_count += 1
                    results.append({
                        "url": url,
                        "status": "failed",
                        "message": "ベクターストアへの追加に失敗"
                    })
                
            except Exception as e:
                logger.error(f"動画処理エラー: {url} - {e}")
                failed_count += 1
                results.append({
                    "url": url,
                    "status": "failed",
                    "message": str(e)
                })
        
        return VideoProcessResponse(
            message=f"処理完了: 成功 {success_count}, 失敗 {failed_count}",
            processed_count=success_count,
            failed_count=failed_count,
            results=results
        )
    
    async def rebuild_task():
        """再構築タスク"""
        logger.info("ベクターストア再構築開始")
        
        try:
            transcripts_dir = app.state.config.get_storage_path('transcripts')
            if app.state.vector_store.rebuild_from_transcripts(transcripts_dir):
                logger.info("ベクターストア再構築完了")
            else:
                logger.error("ベクターストア再構築失敗")
        except Exception as e:
            logger.error(f"再構築タスクエラー: {e}")
    
    return app

# 直接実行用
if __name__ == "__main__":
    config = Config()
    rag_system = RAGSystem(config)
    app = create_app(config, rag_system)
    
    uvicorn.run(
        app,
        host=config.fastapi.host,
        port=config.fastapi.port,
        reload=config.fastapi.reload,
        log_level=config.fastapi.log_level
    )