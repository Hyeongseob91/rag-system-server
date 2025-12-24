/**
 * EvaluationPage Component
 *
 * RAG 평가 메인 페이지
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Play,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Target,
  Clock,
  FileText,
  Sparkles,
} from 'lucide-react';
import { MetricsCard, MetricsGrid } from './MetricsCard';
import { LatencyChart } from './LatencyChart';
import { ProfileSelector } from './ProfileSelector';
import {
  evaluateSingle,
  getProfiles,
  checkEvalHealth,
  exportResultsJson,
  exportResultsCsv,
  downloadBlob,
} from '../../services/evaluationApi';
import type {
  EvaluationResult,
  ProfileInfo,
} from '../../types/evaluation';

export const EvaluationPage: React.FC = () => {
  // State
  const [profiles, setProfiles] = useState<ProfileInfo[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState('hybrid_rerank');
  const [question, setQuestion] = useState('');
  const [groundTruth, setGroundTruth] = useState('');
  const [includeRagas, setIncludeRagas] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<EvaluationResult[]>([]);
  const [ragasAvailable, setRagasAvailable] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load profiles on mount
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [profilesData, healthData] = await Promise.all([
          getProfiles(),
          checkEvalHealth(),
        ]);
        setProfiles(profilesData);
        setRagasAvailable(healthData.ragas_available);
      } catch (err) {
        console.error('Failed to load initial data:', err);
        setError('Failed to load evaluation module');
      }
    };

    loadInitialData();
  }, []);

  // Run evaluation
  const handleEvaluate = useCallback(async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await evaluateSingle({
        question: question.trim(),
        ground_truth: groundTruth.trim() || undefined,
        profile_id: selectedProfileId,
        include_generation_metrics: includeRagas && ragasAvailable,
      });

      setResults((prev) => [result, ...prev]);
    } catch (err: any) {
      console.error('Evaluation failed:', err);
      setError(err.response?.data?.detail || 'Evaluation failed');
    } finally {
      setIsLoading(false);
    }
  }, [question, groundTruth, selectedProfileId, includeRagas, ragasAvailable]);

  // Export results
  const handleExport = async (format: 'json' | 'csv') => {
    if (results.length === 0) return;

    try {
      const blob =
        format === 'json'
          ? await exportResultsJson(results)
          : await exportResultsCsv(results);

      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      downloadBlob(blob, `eval_results_${timestamp}.${format}`);
    } catch (err) {
      console.error('Export failed:', err);
      setError('Export failed');
    }
  };

  // Clear results
  const handleClear = () => {
    setResults([]);
  };

  // Get latest result for display
  const latestResult = results[0];

  return (
    <div className="h-full overflow-auto p-6 bg-gray-50">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              RAG Evaluation
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Test and measure RAG pipeline performance
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* RAGAS Status */}
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs ${
                ragasAvailable
                  ? 'bg-green-100 text-green-700'
                  : 'bg-amber-100 text-amber-700'
              }`}
            >
              {ragasAvailable ? (
                <>
                  <CheckCircle className="w-3.5 h-3.5" />
                  RAGAS Available
                </>
              ) : (
                <>
                  <AlertCircle className="w-3.5 h-3.5" />
                  RAGAS Unavailable
                </>
              )}
            </div>

            {/* Profile Selector */}
            <ProfileSelector
              profiles={profiles}
              selectedId={selectedProfileId}
              onSelect={setSelectedProfileId}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-100 rounded-xl text-red-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Input Section */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Question
              </label>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Enter a question to evaluate..."
                className="w-full h-32 px-4 py-3 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ground Truth (Optional)
              </label>
              <textarea
                value={groundTruth}
                onChange={(e) => setGroundTruth(e.target.value)}
                placeholder="Enter expected answer for RAGAS context_recall..."
                className="w-full h-32 px-4 py-3 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex items-center justify-between mt-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeRagas}
                onChange={(e) => setIncludeRagas(e.target.checked)}
                disabled={!ragasAvailable}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600">
                Include RAGAS metrics (slower)
              </span>
            </label>

            <button
              onClick={handleEvaluate}
              disabled={isLoading || !question.trim()}
              className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Evaluating...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Evaluation
                </>
              )}
            </button>
          </div>
        </div>

        {/* Metrics Display */}
        {latestResult && (
          <>
            {/* Retrieval Metrics */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-800">
                  Retrieval Metrics
                </h2>
              </div>

              <MetricsGrid columns={4}>
                <MetricsCard
                  title="Recall@5"
                  value={latestResult.retrieval_metrics?.recall_at_5 ?? null}
                  target={0.85}
                  subtitle="Top-5 hit rate"
                />
                <MetricsCard
                  title="Recall@10"
                  value={latestResult.retrieval_metrics?.recall_at_10 ?? null}
                  target={0.90}
                  subtitle="Top-10 hit rate"
                />
                <MetricsCard
                  title="nDCG@10"
                  value={latestResult.retrieval_metrics?.ndcg_at_10 ?? null}
                  target={0.75}
                  subtitle="Ranking quality"
                />
                <MetricsCard
                  title="MRR"
                  value={latestResult.retrieval_metrics?.mrr ?? null}
                  target={0.70}
                  subtitle="Mean reciprocal rank"
                />
              </MetricsGrid>
            </div>

            {/* Generation Metrics */}
            {latestResult.generation_metrics && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  <h2 className="text-lg font-semibold text-gray-800">
                    Generation Metrics (RAGAS)
                  </h2>
                </div>

                <MetricsGrid columns={4}>
                  <MetricsCard
                    title="Faithfulness"
                    value={latestResult.generation_metrics.faithfulness}
                    target={0.80}
                    subtitle="Answer fidelity to context"
                  />
                  <MetricsCard
                    title="Answer Relevancy"
                    value={latestResult.generation_metrics.answer_relevancy}
                    target={0.85}
                    subtitle="Answer matches question"
                  />
                  <MetricsCard
                    title="Context Precision"
                    value={latestResult.generation_metrics.context_precision}
                    target={0.70}
                    subtitle="Relevant context ratio"
                  />
                  <MetricsCard
                    title="Context Recall"
                    value={latestResult.generation_metrics.context_recall}
                    target={0.75}
                    subtitle="Required info coverage"
                  />
                </MetricsGrid>
              </div>
            )}

            {/* Latency */}
            <div className="grid grid-cols-3 gap-6">
              <div className="col-span-2">
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="w-5 h-5 text-amber-600" />
                  <h2 className="text-lg font-semibold text-gray-800">
                    Latency Breakdown
                  </h2>
                </div>
                <LatencyChart latency={latestResult.latency} />
              </div>

              <div>
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-5 h-5 text-gray-600" />
                  <h2 className="text-lg font-semibold text-gray-800">
                    Answer Preview
                  </h2>
                </div>
                <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 h-[calc(100%-36px)]">
                  <p className="text-sm text-gray-700 line-clamp-6">
                    {latestResult.answer || 'No answer generated'}
                  </p>
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <span className="text-xs text-gray-400">
                      Profile: {latestResult.profile_id} | Route:{' '}
                      {latestResult.routing_decision}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Results History */}
        {results.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-800">
                Evaluation History ({results.length})
              </h2>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleExport('json')}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <Download className="w-4 h-4" />
                  JSON
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <Download className="w-4 h-4" />
                  CSV
                </button>
                <button
                  onClick={handleClear}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50"
                >
                  <RefreshCw className="w-4 h-4" />
                  Clear
                </button>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Question
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Profile
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      Recall@10
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      nDCG
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      Faithfulness
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      Latency
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {results.map((result, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate">
                        {result.question}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs px-2 py-1 bg-gray-100 rounded-full text-gray-600">
                          {result.profile_id}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-sm">
                        {result.retrieval_metrics
                          ? `${(result.retrieval_metrics.recall_at_10 * 100).toFixed(0)}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-center text-sm">
                        {result.retrieval_metrics
                          ? `${(result.retrieval_metrics.ndcg_at_10 * 100).toFixed(0)}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-center text-sm">
                        {result.generation_metrics?.faithfulness != null
                          ? `${(result.generation_metrics.faithfulness * 100).toFixed(0)}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-center text-sm text-gray-500">
                        {result.latency.total_ms.toFixed(0)}ms
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Empty State */}
        {results.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <Target className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-600">
              No Evaluations Yet
            </h3>
            <p className="text-sm text-gray-400 mt-1">
              Enter a question and click "Run Evaluation" to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
