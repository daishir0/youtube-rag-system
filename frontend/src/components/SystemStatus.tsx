'use client'

import { useState, useEffect } from 'react'
import { RefreshCw, Database, Video, Clock, Server, AlertCircle, CheckCircle } from 'lucide-react'
import { getSystemStatus, getProcessedVideos, rebuildVectorstore, testConnection } from '@/lib/api'
import { translateErrorMessage } from '@/lib/api'
import type { SystemStatus as SystemStatusType } from '@/types'

export default function SystemStatus() {
  const [status, setStatus] = useState<SystemStatusType | null>(null)
  const [processedVideos, setProcessedVideos] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRebuilding, setIsRebuilding] = useState(false)
  const [isConnected, setIsConnected] = useState<boolean | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Test connection
      const connected = await testConnection()
      setIsConnected(connected)

      if (connected) {
        // Fetch system status
        const statusData = await getSystemStatus()
        setStatus(statusData)

        // Fetch processed videos
        const videosData = await getProcessedVideos()
        setProcessedVideos(videosData)
      }

      setLastRefresh(new Date())
    } catch (err) {
      setError(translateErrorMessage(err))
      setIsConnected(false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRebuild = async () => {
    setIsRebuilding(true)
    setError(null)

    try {
      await rebuildVectorstore()
      // Refresh data after rebuild
      setTimeout(() => {
        fetchData()
      }, 2000)
    } catch (err) {
      setError(translateErrorMessage(err))
    } finally {
      setIsRebuilding(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '未設定'
    return new Date(dateString).toLocaleString('ja-JP')
  }

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              システムステータス
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              システムの状態とパフォーマンスを確認
            </p>
          </div>
          <div className="flex items-center space-x-3">
            {lastRefresh && (
              <span className="text-sm text-gray-500">
                最終更新: {formatDate(lastRefresh.toISOString())}
              </span>
            )}
            <button
              onClick={fetchData}
              disabled={isLoading}
              className="btn-secondary flex items-center space-x-2"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span>更新</span>
            </button>
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <div className="card">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${
            isConnected === null ? 'bg-gray-400' : 
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <span className="font-medium">
            {isConnected === null ? 'チェック中...' : 
             isConnected ? 'API接続正常' : 'API接続エラー'}
          </span>
          {isConnected ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : isConnected === false ? (
            <AlertCircle className="h-5 w-5 text-red-500" />
          ) : null}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* System Metrics */}
      {status && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-center">
              <Video className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <div className="text-2xl font-bold text-blue-900">{status.video_count}</div>
                <div className="text-sm text-blue-600">処理済み動画</div>
              </div>
            </div>
          </div>

          <div className="card bg-green-50 border-green-200">
            <div className="flex items-center">
              <Database className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <div className="text-2xl font-bold text-green-900">{status.document_count}</div>
                <div className="text-sm text-green-600">ドキュメント</div>
              </div>
            </div>
          </div>

          <div className="card bg-purple-50 border-purple-200">
            <div className="flex items-center">
              <Server className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <div className="text-2xl font-bold text-purple-900">{status.processed_urls}</div>
                <div className="text-sm text-purple-600">処理済みURL</div>
              </div>
            </div>
          </div>

          <div className="card bg-orange-50 border-orange-200">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-orange-600" />
              <div className="ml-3">
                <div className="text-sm font-bold text-orange-900">
                  {status.last_updated ? '最近' : '未更新'}
                </div>
                <div className="text-sm text-orange-600">最終更新</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Status */}
      {status && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            詳細情報
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">システム状態</div>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  status.status === 'active' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm">{status.status === 'active' ? '稼働中' : '停止中'}</span>
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">最終更新日時</div>
              <div className="text-sm">{formatDate(status.last_updated)}</div>
            </div>
          </div>
        </div>
      )}

      {/* Processed Videos Summary */}
      {processedVideos && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            処理済み動画の概要
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">総動画数</div>
              <div className="text-2xl font-bold text-gray-900">{processedVideos.total_count}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">データ更新</div>
              <div className="text-sm">{formatDate(processedVideos.timestamp)}</div>
            </div>
          </div>
        </div>
      )}

      {/* System Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          システム操作
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <div className="font-medium text-gray-900">ベクターストア再構築</div>
              <div className="text-sm text-gray-600">
                字幕ファイルが更新された場合にベクターストアを再構築します
              </div>
            </div>
            <button
              onClick={handleRebuild}
              disabled={isRebuilding || !isConnected}
              className="btn-secondary flex items-center space-x-2"
            >
              {isRebuilding ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>再構築中...</span>
                </>
              ) : (
                <>
                  <Database className="h-4 w-4" />
                  <span>再構築</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && !status && (
        <div className="card text-center py-8">
          <RefreshCw className="h-8 w-8 text-gray-400 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">システム状態を取得中...</p>
        </div>
      )}

      {/* Tips */}
      <div className="card bg-yellow-50 border-yellow-200">
        <h3 className="text-lg font-semibold text-yellow-900 mb-3">
          💡 システム管理のヒント
        </h3>
        <ul className="text-sm text-yellow-800 space-y-2">
          <li>• 字幕ファイルを手動で編集した場合は、ベクターストアの再構築を実行してください</li>
          <li>• システムの応答が遅い場合は、処理中の動画がないか確認してください</li>
          <li>• 定期的にシステム状態を確認し、異常がないかチェックしてください</li>
          <li>• 大量の動画を処理する場合は、システムリソースの使用量にご注意ください</li>
        </ul>
      </div>
    </div>
  )
}