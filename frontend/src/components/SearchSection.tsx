'use client'

import { useState } from 'react'
import { Search, ExternalLink, Clock, User, Star } from 'lucide-react'
import { searchVideos, getSimilarVideos } from '@/lib/api'
import { translateErrorMessage } from '@/lib/api'
import type { SearchResult, SimilarVideo } from '@/types'

export default function SearchSection() {
  const [query, setQuery] = useState('')
  const [maxResults, setMaxResults] = useState(5)
  const [results, setResults] = useState<SearchResult[]>([])
  const [similarVideos, setSimilarVideos] = useState<SimilarVideo[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'content' | 'videos'>('content')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) {
      setError('検索クエリを入力してください')
      return
    }

    setIsLoading(true)
    setError(null)
    setResults([])
    setSimilarVideos([])

    try {
      if (activeTab === 'content') {
        const response = await searchVideos(query, maxResults)
        setResults(response.results)
      } else {
        const response = await getSimilarVideos(query, maxResults)
        setSimilarVideos(response.similar_videos)
      }
    } catch (err) {
      setError(translateErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const formatScore = (score: number): string => {
    return `${(score * 100).toFixed(1)}%`
  }

  const formatTimestamp = (timestamp: string): string => {
    return timestamp.replace(/(\d+)秒/, '$1s').replace(/(\d+)分/, '$1m').replace(/(\d+)時間/, '$1h')
  }

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          動画検索
        </h2>
        
        {/* Search Type Tabs */}
        <div className="flex space-x-4 mb-4">
          <button
            onClick={() => setActiveTab('content')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'content'
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            内容で検索
          </button>
          <button
            onClick={() => setActiveTab('videos')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'videos'
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            類似動画検索
          </button>
        </div>

        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              検索クエリ
            </label>
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="input"
              placeholder={
                activeTab === 'content' 
                  ? "動画の内容で検索 (例: 機械学習の基本概念)"
                  : "類似動画を検索 (例: Python プログラミング)"
              }
              disabled={isLoading}
            />
          </div>

          <div>
            <label htmlFor="maxResults" className="block text-sm font-medium text-gray-700 mb-2">
              最大結果数
            </label>
            <select
              id="maxResults"
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="input"
              disabled={isLoading}
            >
              <option value={5}>5件</option>
              <option value={10}>10件</option>
              <option value={15}>15件</option>
              <option value={20}>20件</option>
            </select>
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
                <span>検索中...</span>
              </>
            ) : (
              <>
                <Search className="h-5 w-5" />
                <span>検索</span>
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
              <div className="w-5 h-5 rounded-full bg-red-400 flex items-center justify-center">
                <span className="text-white text-xs">!</span>
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Content Search Results */}
      {activeTab === 'content' && results.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            検索結果 ({results.length} 件)
          </h3>
          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 mb-2">{result.title}</h4>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                      <div className="flex items-center space-x-1">
                        <User className="h-4 w-4" />
                        <span>{result.uploader}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="h-4 w-4" />
                        <span>{formatTimestamp(result.timestamp)}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Star className="h-4 w-4 text-yellow-500" />
                        <span>{formatScore(result.score)}</span>
                      </div>
                    </div>
                    <p className="text-gray-700 text-sm mb-3">{result.content}</p>
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-primary-600 hover:text-primary-700 text-sm"
                    >
                      <ExternalLink className="h-4 w-4" />
                      <span>動画を見る</span>
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Similar Videos Results */}
      {activeTab === 'videos' && similarVideos.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            類似動画 ({similarVideos.length} 件)
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {similarVideos.map((video, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <h4 className="font-medium text-gray-900 mb-2">{video.title}</h4>
                <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                  <div className="flex items-center space-x-1">
                    <User className="h-4 w-4" />
                    <span>{video.uploader}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Star className="h-4 w-4 text-yellow-500" />
                    <span>{formatScore(video.max_score)}</span>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mb-3">
                  {video.chunk_count} セグメント・平均類似度: {formatScore(video.avg_score)}
                </div>
                <a
                  href={video.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 text-primary-600 hover:text-primary-700 text-sm"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>動画を見る</span>
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!isLoading && !error && (
        (activeTab === 'content' && results.length === 0 && query) ||
        (activeTab === 'videos' && similarVideos.length === 0 && query)
      ) && (
        <div className="card text-center py-8">
          <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">検索結果が見つかりませんでした。</p>
          <p className="text-gray-500 text-sm mt-2">
            別のキーワードで検索してみてください。
          </p>
        </div>
      )}
    </div>
  )
}