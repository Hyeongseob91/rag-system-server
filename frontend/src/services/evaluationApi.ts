/**
 * Evaluation API Service
 *
 * RAG 평가 관련 API 호출
 */

import axios from 'axios';
import type {
  EvaluationResult,
  BatchEvaluationResult,
  ProfileInfo,
  SingleEvalRequest,
  BatchEvalRequest,
} from '../types/evaluation';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8188';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes (RAGAS can be slow)
});

/**
 * 단일 쿼리 평가
 */
export const evaluateSingle = async (
  request: SingleEvalRequest
): Promise<EvaluationResult> => {
  const response = await apiClient.post<EvaluationResult>(
    '/api/v1/eval/single',
    request
  );
  return response.data;
};

/**
 * 배치 평가
 */
export const evaluateBatch = async (
  request: BatchEvalRequest
): Promise<BatchEvaluationResult> => {
  const response = await apiClient.post<BatchEvaluationResult>(
    '/api/v1/eval/batch',
    request
  );
  return response.data;
};

/**
 * 사용 가능한 프로파일 목록 조회
 */
export const getProfiles = async (): Promise<ProfileInfo[]> => {
  const response = await apiClient.get<ProfileInfo[]>('/api/v1/eval/profiles');
  return response.data;
};

/**
 * 특정 프로파일 상세 정보 조회
 */
export const getProfileDetail = async (profileId: string): Promise<ProfileInfo> => {
  const response = await apiClient.get<ProfileInfo>(
    `/api/v1/eval/profiles/${profileId}`
  );
  return response.data;
};

/**
 * 평가 모듈 상태 확인
 */
export const checkEvalHealth = async (): Promise<{
  status: string;
  ragas_available: boolean;
  profiles_count: number;
}> => {
  const response = await apiClient.get('/api/v1/eval/health');
  return response.data;
};

/**
 * 결과를 JSON으로 내보내기
 */
export const exportResultsJson = async (
  results: EvaluationResult[]
): Promise<Blob> => {
  const response = await apiClient.post('/api/v1/eval/export/json', results, {
    responseType: 'blob',
  });
  return response.data;
};

/**
 * 결과를 CSV로 내보내기
 */
export const exportResultsCsv = async (
  results: EvaluationResult[]
): Promise<Blob> => {
  const response = await apiClient.post('/api/v1/eval/export/csv', results, {
    responseType: 'blob',
  });
  return response.data;
};

/**
 * Blob 다운로드 헬퍼
 */
export const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
