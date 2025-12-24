/**
 * LatencyChart Component
 *
 * 지연 시간 Breakdown을 시각화
 */

import React from 'react';
import type { LatencyBreakdown } from '../../types/evaluation';

interface LatencyChartProps {
  latency: LatencyBreakdown;
}

export const LatencyChart: React.FC<LatencyChartProps> = ({ latency }) => {
  const segments = [
    {
      name: 'Query Rewrite',
      value: latency.query_rewrite_ms,
      color: 'bg-blue-500',
    },
    {
      name: 'Retrieval',
      value: latency.retrieval_ms,
      color: 'bg-green-500',
    },
    {
      name: 'Reranking',
      value: latency.rerank_ms,
      color: 'bg-amber-500',
    },
    {
      name: 'Generation',
      value: latency.generation_ms,
      color: 'bg-purple-500',
    },
  ];

  const total = latency.total_ms;

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <h3 className="text-sm font-medium text-gray-700 mb-4">
        Latency Breakdown
      </h3>

      {/* Stacked Bar */}
      <div className="h-8 flex rounded-lg overflow-hidden mb-4">
        {segments.map((seg, idx) => {
          const width = (seg.value / total) * 100;
          if (width < 1) return null;
          return (
            <div
              key={idx}
              className={`${seg.color} transition-all duration-300`}
              style={{ width: `${width}%` }}
              title={`${seg.name}: ${seg.value.toFixed(0)}ms (${width.toFixed(1)}%)`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-2">
        {segments.map((seg, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded ${seg.color}`} />
            <span className="text-xs text-gray-600">
              {seg.name}: {seg.value.toFixed(0)}ms
            </span>
          </div>
        ))}
      </div>

      {/* Total */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Total</span>
          <span className="text-lg font-bold text-gray-800">
            {total.toFixed(0)}ms
          </span>
        </div>
      </div>
    </div>
  );
};

interface LatencyComparisonProps {
  profiles: Array<{
    name: string;
    latency: LatencyBreakdown;
  }>;
}

export const LatencyComparison: React.FC<LatencyComparisonProps> = ({
  profiles,
}) => {
  const maxTotal = Math.max(...profiles.map((p) => p.latency.total_ms));

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <h3 className="text-sm font-medium text-gray-700 mb-4">
        Profile Latency Comparison
      </h3>

      <div className="space-y-3">
        {profiles.map((profile, idx) => {
          const width = (profile.latency.total_ms / maxTotal) * 100;
          return (
            <div key={idx}>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>{profile.name}</span>
                <span>{profile.latency.total_ms.toFixed(0)}ms</span>
              </div>
              <div className="h-4 bg-gray-100 rounded overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                  style={{ width: `${width}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
