import axios from 'axios';
import type { QueryResponse, UploadResponse } from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8188';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

interface BackendQueryResponse {
  answer: string;
  sources: Array<{ content: string; source?: string; score?: number }>;
  processing_time_ms: number;
}

export const sendQuery = async (question: string): Promise<QueryResponse> => {
  const response = await apiClient.post<BackendQueryResponse>('/api/v1/query', {
    question,
  });
  return {
    answer: response.data.answer,
    sources: response.data.sources?.map(s => s.content),
  };
};

interface BackendUploadResponse {
  task_id: string;
  file_name: string;
  status: string;
  message: string;
}

interface BackendUploadStatusResponse {
  task_id: string;
  status: string;
  file_name: string;
  chunks_created?: number;
  error?: string;
  completed_at?: string;
}

const pollUploadStatus = async (taskId: string, maxAttempts = 60): Promise<BackendUploadStatusResponse> => {
  for (let i = 0; i < maxAttempts; i++) {
    const response = await apiClient.get<BackendUploadStatusResponse>(`/api/v1/upload/${taskId}`);
    if (response.data.status === 'completed' || response.data.status === 'failed') {
      return response.data;
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  throw new Error('Upload timeout');
};

export const uploadDocument = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const uploadResponse = await apiClient.post<BackendUploadResponse>(
    '/api/v1/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  // Poll for completion
  const statusResponse = await pollUploadStatus(uploadResponse.data.task_id);

  if (statusResponse.status === 'failed') {
    throw new Error(statusResponse.error || 'Upload failed');
  }

  return {
    success: true,
    message: 'Upload completed',
    data: {
      file_name: statusResponse.file_name,
      chunks_created: statusResponse.chunks_created || 0,
      doc_id: statusResponse.task_id,
    },
  };
};

export const checkHealth = async (): Promise<boolean> => {
  try {
    const response = await apiClient.get('/health');
    return response.data.status === 'ok';
  } catch {
    return false;
  }
};

interface HealthDetailResponse {
  status: string;
  qdrant_connected: boolean;
  document_count: number;
  version: string;
}

export const getHealthDetail = async (): Promise<HealthDetailResponse> => {
  const response = await apiClient.get<HealthDetailResponse>('/api/v1/health');
  return response.data;
};
