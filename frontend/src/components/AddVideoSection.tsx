'use client'

import { useState } from 'react'
import { Plus, Youtube, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { addVideosSync, isValidYouTubeUrl } from '@/lib/api'
import { translateErrorMessage } from '@/lib/api'
import type { VideoProcessResponse } from '@/types'

export default function AddVideoSection() {
  const [urls, setUrls] = useState<string[]>([''])
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<VideoProcessResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const addUrlField = () => {
    setUrls([...urls, ''])
  }

  const removeUrlField = (index: number) => {
    if (urls.length > 1) {
      setUrls(urls.filter((_, i) => i !== index))
    }
  }

  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls]
    newUrls[index] = value
    setUrls(newUrls)
  }

  const validateUrls = (): string[] => {
    const validUrls = urls.filter(url => url.trim() !== '')
    const invalidUrls = validUrls.filter(url => !isValidYouTubeUrl(url))
    
    if (invalidUrls.length > 0) {
      throw new Error(`無効なYouTube URLが含まれています: ${invalidUrls.join(', ')}`)
    }
    
    return validUrls
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const validUrls = validateUrls()
      
      if (validUrls.length === 0) {
        throw new Error('少なくとも1つのURLを入力してください')
      }

      const response = await addVideosSync(validUrls)
      setResult(response)
      
      // Clear form on success
      if (response.processed_count > 0) {
        setUrls([''])
      }
    } catch (err) {
      setError(translateErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'skipped':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'failed':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'skipped':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      {/* Add Video Form */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          YouTube動画の追加
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              YouTube動画のURL
            </label>
            <div className="space-y-2">
              {urls.map((url, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div className="flex-1">
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => updateUrl(index, e.target.value)}
                      className="input"
                      placeholder="https://www.youtube.com/watch?v=..."
                      disabled={isLoading}
                    />
                  </div>
                  {urls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeUrlField(index)}
                      className="btn-secondary p-2"
                      disabled={isLoading}
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            
            <button
              type="button"
              onClick={addUrlField}
              className="btn-secondary mt-2 flex items-center space-x-2"
              disabled={isLoading}
            >
              <Plus className="h-4 w-4" />
              <span>URLを追加</span>
            </button>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">使用方法</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• YouTube動画のURLを入力してください</li>
              <li>• 複数のURLを一度に追加することができます</li>
              <li>• 既に処理済みの動画は自動的にスキップされます</li>
              <li>• 処理には時間がかかる場合があります</li>
            </ul>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary flex items-center space-x-2"
          >
            {isLoading ? (
              <>
                <div className="loading-dots">
                  <div></div>
                  <div></div>
                  <div></div>
                </div>
                <span>処理中...</span>
              </>
            ) : (
              <>
                <Youtube className="h-5 w-5" />
                <span>動画を追加</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Error Display */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex">
            <div className="flex-shrink-0">
              <XCircle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Processing Results */}
      {result && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            処理結果
          </h3>
          
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="text-2xl font-bold text-green-700">{result.processed_count}</div>
              <div className="text-sm text-green-600">成功</div>
            </div>
            <div className="text-center p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="text-2xl font-bold text-red-700">{result.failed_count}</div>
              <div className="text-sm text-red-600">失敗</div>
            </div>
            <div className="text-center p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-2xl font-bold text-blue-700">{result.results.length}</div>
              <div className="text-sm text-blue-600">合計</div>
            </div>
          </div>

          {/* Detailed Results */}
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">詳細結果</h4>
            {result.results.map((video, index) => (
              <div key={index} className={`border rounded-lg p-4 ${getStatusColor(video.status)}`}>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    {getStatusIcon(video.status)}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{video.title || 'タイトル取得失敗'}</div>
                    <div className="text-sm mt-1 break-all">{video.url}</div>
                    <div className="text-sm mt-1">{video.message}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="card bg-gray-50 border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          💡 ヒント
        </h3>
        <ul className="text-sm text-gray-700 space-y-2">
          <li>• 動画の字幕が利用できない場合は処理に失敗します</li>
          <li>• 日本語または英語の字幕が自動的に検索されます</li>
          <li>• 処理が完了した動画は検索・質問応答で利用できます</li>
          <li>• 大量の動画を処理する場合は時間をおいて実行してください</li>
        </ul>
      </div>
    </div>
  )
}