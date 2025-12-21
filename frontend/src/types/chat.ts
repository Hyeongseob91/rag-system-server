export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
}

export interface QueryResponse {
  answer: string;
  sources?: string[];
}

export interface UploadResponse {
  success: boolean;
  message: string;
  data: {
    file_name: string;
    chunks_created: number;
    doc_id: string;
  };
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  chunks: number;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  uploadedAt: Date;
}

export interface TokenUsage {
  timestamp: string;
  prompt: number;
  completion: number;
}
