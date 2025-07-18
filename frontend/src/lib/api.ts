import axios from 'axios'
import type {
  SearchResponse,
  AnswerResponse,
  VideoProcessResponse,
  SystemStatus,
  SimilarVideosResponse,
  VideoSummary,
} from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error)
    
    // Handle network errors
    if (!error.response) {
      throw new Error('ネットワークエラー: サーバーに接続できません')
    }
    
    // Handle HTTP errors
    const status = error.response.status
    const message = error.response.data?.detail || error.message
    
    switch (status) {
      case 400:
        throw new Error(`リクエストエラー: ${message}`)
      case 404:
        throw new Error(`見つかりません: ${message}`)
      case 500:
        throw new Error(`サーバーエラー: ${message}`)
      default:
        throw new Error(`エラー (${status}): ${message}`)
    }
  }
)

// API Functions

/**
 * システムの状態を取得
 */
export const getSystemStatus = async (): Promise<SystemStatus> => {
  const response = await api.get<SystemStatus>('/status')
  return response.data
}

/**
 * 動画を検索
 */
export const searchVideos = async (
  query: string,
  maxResults: number = 5
): Promise<SearchResponse> => {
  const response = await api.post<SearchResponse>('/search', {
    query,
    max_results: maxResults,
  })
  return response.data
}

/**
 * 質問に回答
 */
export const askQuestion = async (
  question: string,
  maxResults: number = 5
): Promise<AnswerResponse> => {
  const response = await api.post<AnswerResponse>('/question', {
    question,
    max_results: maxResults,
  })
  return response.data
}

/**
 * 動画URLを追加（同期処理）
 */
export const addVideosSync = async (urls: string[]): Promise<VideoProcessResponse> => {
  const response = await api.post<VideoProcessResponse>('/videos/add-sync', {
    urls,
  })
  return response.data
}

/**
 * 動画URLを追加（非同期処理）
 */
export const addVideosAsync = async (urls: string[]): Promise<VideoProcessResponse> => {
  const response = await api.post<VideoProcessResponse>('/videos/add', {
    urls,
  })
  return response.data
}

/**
 * 類似動画を取得
 */
export const getSimilarVideos = async (
  query: string,
  limit: number = 10
): Promise<SimilarVideosResponse> => {
  const response = await api.get<SimilarVideosResponse>(
    `/videos/similar?query=${encodeURIComponent(query)}&limit=${limit}`
  )
  return response.data
}

/**
 * 動画の要約を取得
 */
export const getVideoSummary = async (videoId: string): Promise<VideoSummary> => {
  const response = await api.get<VideoSummary>(`/videos/${videoId}/summary`)
  return response.data
}

/**
 * 処理済み動画のリストを取得
 */
export const getProcessedVideos = async (): Promise<any> => {
  const response = await api.get('/videos/processed')
  return response.data
}

/**
 * 動画を削除
 */
export const deleteVideo = async (videoId: string): Promise<any> => {
  const response = await api.delete(`/videos/${videoId}`)
  return response.data
}

/**
 * ベクターストアを再構築
 */
export const rebuildVectorstore = async (): Promise<any> => {
  const response = await api.post('/rebuild')
  return response.data
}

/**
 * ヘルスチェック
 */
export const healthCheck = async (): Promise<any> => {
  const response = await api.get('/health')
  return response.data
}

/**
 * APIの接続テスト
 */
export const testConnection = async (): Promise<boolean> => {
  try {
    await healthCheck()
    return true
  } catch (error) {
    console.error('API接続テストに失敗:', error)
    return false
  }
}

/**
 * YouTube URLの妥当性チェック
 */
export const isValidYouTubeUrl = (url: string): boolean => {
  const patterns = [
    /^https?:\/\/(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)/,
    /^https?:\/\/(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]+)/,
    /^https?:\/\/(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]+)/,
    /^https?:\/\/(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]+)/,
  ]
  
  return patterns.some(pattern => pattern.test(url))
}

/**
 * YouTube URLからビデオIDを抽出
 */
export const extractVideoId = (url: string): string | null => {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]+)/,
  ]
  
  for (const pattern of patterns) {
    const match = url.match(pattern)
    if (match && match[1]) {
      return match[1]
    }
  }
  
  return null
}

/**
 * エラーメッセージを日本語に変換
 */
export const translateErrorMessage = (error: any): string => {
  if (typeof error === 'string') {
    return error
  }
  
  if (error.message) {
    return error.message
  }
  
  // Network errors
  if (error.code === 'ECONNREFUSED' || error.code === 'NETWORK_ERROR') {
    return 'サーバーに接続できません。サーバーが起動しているか確認してください。'
  }
  
  // Timeout errors
  if (error.code === 'ECONNABORTED') {
    return 'リクエストがタイムアウトしました。もう一度お試しください。'
  }
  
  return '予期しないエラーが発生しました。'
}

export default api