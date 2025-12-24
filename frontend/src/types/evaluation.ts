/**
 * Evaluation Types
 *
 * RAG 평가 관련 타입 정의
 */

export interface RetrievalMetrics {
  recall_at_5: number;
  recall_at_10: number;
  ndcg_at_10: number;
  mrr: number;
  hit_at_5: boolean;
  hit_at_10: boolean;
}

export interface GenerationMetrics {
  faithfulness: number | null;
  answer_relevancy: number | null;
  context_precision: number | null;
  context_recall: number | null;
}

export interface LatencyBreakdown {
  total_ms: number;
  query_rewrite_ms: number;
  retrieval_ms: number;
  rerank_ms: number;
  generation_ms: number;
}

export interface RetrievedDocument {
  doc_id: string;
  content: string;
  score: number;
  rank: number;
}

export interface EvaluationResult {
  question: string;
  answer: string;
  ground_truth: string | null;
  retrieved_docs: RetrievedDocument[];
  retrieval_metrics: RetrievalMetrics | null;
  generation_metrics: GenerationMetrics | null;
  latency: LatencyBreakdown;
  profile_id: string;
  routing_decision: string;
}

export interface AggregatedMetrics {
  // Retrieval
  avg_recall_at_5: number;
  avg_recall_at_10: number;
  avg_ndcg_at_10: number;
  avg_mrr: number;
  hit_rate_at_5: number;
  hit_rate_at_10: number;
  // Generation
  avg_faithfulness: number | null;
  avg_answer_relevancy: number | null;
  avg_context_precision: number | null;
  avg_context_recall: number | null;
  // Latency
  avg_total_latency_ms: number;
  avg_retrieval_latency_ms: number;
  avg_rerank_latency_ms: number;
  avg_generation_latency_ms: number;
  // Count
  total_samples: number;
}

export interface BatchEvaluationResult {
  results: EvaluationResult[];
  aggregated: AggregatedMetrics;
  profile_id: string;
}

export interface ProfileInfo {
  id: string;
  name: string;
  description: string;
  retriever_type: string;
  use_reranker: boolean;
  use_query_rewrite: boolean;
}

export interface SingleEvalRequest {
  question: string;
  ground_truth?: string;
  relevant_doc_ids?: string[];
  profile_id: string;
  include_generation_metrics: boolean;
}

export interface BatchEvalRequest {
  items: SingleEvalRequest[];
  profile_id: string;
  include_generation_metrics: boolean;
}
