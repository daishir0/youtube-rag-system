'use client'

import { useState } from 'react'
import { Search, Plus, Database, MessageCircle, Youtube, Sparkles } from 'lucide-react'
import SearchSection from '@/components/SearchSection'
import AddVideoSection from '@/components/AddVideoSection'
import SystemStatus from '@/components/SystemStatus'
import ChatSection from '@/components/ChatSection'

type TabType = 'search' | 'add' | 'chat' | 'status'

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>('search')

  const tabs = [
    { id: 'search', name: '検索', icon: Search },
    { id: 'add', name: '動画追加', icon: Plus },
    { id: 'chat', name: '質問応答', icon: MessageCircle },
    { id: 'status', name: 'ステータス', icon: Database },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <Youtube className="h-8 w-8 text-red-600" />
                <Sparkles className="h-6 w-6 text-primary-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">YouTube RAG System</h1>
                <p className="text-sm text-gray-600">AI-powered video search & Q&A</p>
              </div>
            </div>
            <div className="hidden md:flex items-center space-x-2">
              <div className="h-2 w-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">システム稼働中</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="hidden sm:inline">{tab.name}</span>
                </button>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-fade-in">
          {activeTab === 'search' && <SearchSection />}
          {activeTab === 'add' && <AddVideoSection />}
          {activeTab === 'chat' && <ChatSection />}
          {activeTab === 'status' && <SystemStatus />}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 sm:mb-0">
              <Youtube className="h-5 w-5 text-red-600" />
              <span className="text-sm text-gray-600">YouTube RAG System v1.0</span>
            </div>
            <div className="flex items-center space-x-6 text-sm text-gray-600">
              <a href="#" className="hover:text-gray-900 transition-colors">使い方</a>
              <a href="#" className="hover:text-gray-900 transition-colors">お問い合わせ</a>
              <a href="#" className="hover:text-gray-900 transition-colors">GitHub</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}