// API Response Types
export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  error?: string;
}

// Video Types
export interface Video {
  video_id: string;
  title: string;
  uploader: string;
  url: string;
  timestamp_url?: string;
  upload_date?: string;
  duration?: number;
  view_count?: number;
  channel_id?: string;
  channel_url?: string;
}

// Search Types
export interface SearchResult {
  title: string;
  uploader: string;
  url: string;
  content: string;
  score: number;
  timestamp: string;
  video_id: string;
  chunk_id: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  timestamp: string;
}

// Question & Answer Types
export interface QuestionSource {
  title: string;
  uploader: string;
  url: string;
  timestamp: string;
  score: number;
  content: string;
  video_id: string;
  chunk_id: number;
}

export interface AnswerResponse {
  question: string;
  answer: string;
  sources: QuestionSource[];
  timestamp: string;
  context_used: number;
}

// Video Processing Types
export interface ProcessedVideo {
  url: string;
  status: 'success' | 'failed' | 'skipped';
  message: string;
  title?: string;
}

export interface VideoProcessResponse {
  message: string;
  processed_count: number;
  failed_count: number;
  results: ProcessedVideo[];
}

// System Status Types
export interface SystemStatus {
  status: string;
  video_count: number;
  document_count: number;
  processed_urls: number;
  last_updated: string | null;
}

// Similar Videos Types
export interface SimilarVideo {
  title: string;
  uploader: string;
  url: string;
  video_id: string;
  max_score: number;
  avg_score: number;
  chunk_count: number;
}

export interface SimilarVideosResponse {
  query: string;
  similar_videos: SimilarVideo[];
  total_results: number;
  timestamp: string;
}

// Video Summary Types
export interface VideoSummary {
  video_id: string;
  title: string;
  uploader: string;
  url: string;
  summary: string;
  generated_at: string;
}

// Form Types
export interface AddVideoForm {
  urls: string[];
}

export interface SearchForm {
  query: string;
  maxResults: number;
}

export interface QuestionForm {
  question: string;
  maxResults: number;
}

// UI State Types
export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface ErrorState {
  hasError: boolean;
  message?: string;
}

// Chat Types
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: QuestionSource[];
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error?: string;
}