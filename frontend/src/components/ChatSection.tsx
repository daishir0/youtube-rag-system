'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, User, Bot, ExternalLink, Clock, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { askQuestion } from '@/lib/api'
import { translateErrorMessage } from '@/lib/api'
import type { ChatMessage, QuestionSource } from '@/types'

export default function ChatSection() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await askQuestion(input.trim(), 5)
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        timestamp: response.timestamp,
        sources: response.sources,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError(translateErrorMessage(err))
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `申し訳ありませんが、エラーが発生しました: ${translateErrorMessage(err)}`,
        timestamp: new Date().toISOString(),
      }

      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatSourceTimestamp = (timestamp: string): string => {
    return timestamp.replace(/(\d+)秒/, '$1s').replace(/(\d+)分/, '$1m').replace(/(\d+)時間/, '$1h')
  }

  const clearChat = () => {
    setMessages([])
    setError(null)
  }

  return (
    <div className="space-y-6">
      {/* Chat Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              AI質問応答チャット
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              YouTube動画の内容について質問してください
            </p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="btn-secondary text-sm"
            >
              チャットをクリア
            </button>
          )}
        </div>
      </div>

      {/* Chat Messages */}
      <div className="card min-h-[400px] max-h-[600px] overflow-y-auto">
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">
                YouTube動画の内容について質問してください
              </p>
              <p className="text-gray-500 text-sm mt-2">
                例: 「機械学習の基本概念について教えて」
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl flex space-x-3 ${
                    message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  {/* Avatar */}
                  <div className={`flex-shrink-0 ${
                    message.type === 'user' ? 'order-2' : 'order-1'
                  }`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.type === 'user' 
                        ? 'bg-primary-600 text-white' 
                        : 'bg-gray-600 text-white'
                    }`}>
                      {message.type === 'user' ? (
                        <User className="h-5 w-5" />
                      ) : (
                        <Bot className="h-5 w-5" />
                      )}
                    </div>
                  </div>

                  {/* Message Content */}
                  <div className={`flex-1 ${
                    message.type === 'user' ? 'order-1' : 'order-2'
                  }`}>
                    <div className={`rounded-lg p-4 ${
                      message.type === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}>
                      {message.type === 'user' ? (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      ) : (
                        <ReactMarkdown 
                          className="prose prose-sm max-w-none"
                          components={{
                            p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                            ul: ({ children }) => <ul className="mb-3 last:mb-0 list-disc pl-5">{children}</ul>,
                            ol: ({ children }) => <ol className="mb-3 last:mb-0 list-decimal pl-5">{children}</ol>,
                            li: ({ children }) => <li className="mb-1">{children}</li>,
                            code: ({ children }) => (
                              <code className="bg-gray-200 px-1 py-0.5 rounded text-sm">{children}</code>
                            ),
                            pre: ({ children }) => (
                              <pre className="bg-gray-200 p-2 rounded text-sm overflow-x-auto">{children}</pre>
                            ),
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      )}
                    </div>

                    {/* Timestamp */}
                    <div className={`text-xs text-gray-500 mt-1 ${
                      message.type === 'user' ? 'text-right' : 'text-left'
                    }`}>
                      {formatTimestamp(message.timestamp)}
                    </div>

                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <div className="flex items-center space-x-2 text-sm font-medium text-gray-700">
                          <Sparkles className="h-4 w-4" />
                          <span>参考動画</span>
                        </div>
                        {message.sources.map((source, index) => (
                          <div key={index} className="bg-white border border-gray-200 rounded-lg p-3 text-sm">
                            <div className="font-medium text-gray-900 mb-1">
                              {source.title}
                            </div>
                            <div className="flex items-center space-x-4 text-gray-600 mb-2">
                              <span>{source.uploader}</span>
                              <div className="flex items-center space-x-1">
                                <Clock className="h-3 w-3" />
                                <span>{formatSourceTimestamp(source.timestamp)}</span>
                              </div>
                              <div className="flex items-center space-x-1">
                                <span className="text-yellow-500">★</span>
                                <span>{(source.score * 100).toFixed(1)}%</span>
                              </div>
                            </div>
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center space-x-1 text-primary-600 hover:text-primary-700"
                            >
                              <ExternalLink className="h-3 w-3" />
                              <span>動画を見る</span>
                            </a>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex space-x-3">
                <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                  <Bot className="h-5 w-5 text-white" />
                </div>
                <div className="bg-gray-100 rounded-lg p-4">
                  <div className="loading-dots">
                    <div></div>
                    <div></div>
                    <div></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="card">
        <div className="flex space-x-3">
          <div className="flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="質問を入力してください..."
              className="input"
              disabled={isLoading}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="btn-primary flex items-center space-x-2"
          >
            <Send className="h-5 w-5" />
            <span className="hidden sm:inline">送信</span>
          </button>
        </div>
      </form>

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

      {/* Usage Tips */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          💡 使い方のヒント
        </h3>
        <ul className="text-sm text-blue-800 space-y-2">
          <li>• 具体的な質問をすることで、より適切な回答が得られます</li>
          <li>• 複数の動画から情報を統合した回答が提供されます</li>
          <li>• 参考動画のリンクから該当部分を直接確認できます</li>
          <li>• 質問に関連する動画が見つからない場合は、その旨が回答されます</li>
        </ul>
      </div>
    </div>
  )
}