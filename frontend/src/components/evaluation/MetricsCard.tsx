/**
 * MetricsCard Component
 *
 * 개별 메트릭 값을 카드 형태로 표시
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricsCardProps {
  title: string;
  value: number | null;
  subtitle?: string;
  format?: 'percent' | 'number' | 'ms';
  target?: number;
  icon?: React.ReactNode;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  subtitle,
  format = 'percent',
  target,
  icon,
}) => {
  const formatValue = (val: number | null): string => {
    if (val === null) return 'N/A';

    switch (format) {
      case 'percent':
        return `${(val * 100).toFixed(1)}%`;
      case 'ms':
        return `${val.toFixed(0)}ms`;
      case 'number':
        return val.toFixed(2);
      default:
        return val.toString();
    }
  };

  const getStatusColor = (): string => {
    if (value === null || target === undefined) return 'text-gray-600';
    if (format === 'ms') {
      // Lower is better for latency
      return value <= target ? 'text-green-600' : 'text-amber-600';
    }
    // Higher is better for other metrics
    return value >= target ? 'text-green-600' : 'text-amber-600';
  };

  const getTrendIcon = () => {
    if (value === null || target === undefined) {
      return <Minus className="w-4 h-4 text-gray-400" />;
    }

    if (format === 'ms') {
      return value <= target ? (
        <TrendingDown className="w-4 h-4 text-green-500" />
      ) : (
        <TrendingUp className="w-4 h-4 text-amber-500" />
      );
    }

    return value >= target ? (
      <TrendingUp className="w-4 h-4 text-green-500" />
    ) : (
      <TrendingDown className="w-4 h-4 text-amber-500" />
    );
  };

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">{title}</span>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>

      <div className="flex items-end gap-2">
        <span className={`text-2xl font-bold ${getStatusColor()}`}>
          {formatValue(value)}
        </span>
        {target !== undefined && (
          <div className="flex items-center gap-1 mb-1">
            {getTrendIcon()}
            <span className="text-xs text-gray-400">
              목표: {formatValue(target)}
            </span>
          </div>
        )}
      </div>

      {subtitle && (
        <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
      )}
    </div>
  );
};

interface MetricsGridProps {
  children: React.ReactNode;
  columns?: 2 | 3 | 4;
}

export const MetricsGrid: React.FC<MetricsGridProps> = ({
  children,
  columns = 4,
}) => {
  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  };

  return (
    <div className={`grid ${gridCols[columns]} gap-4`}>
      {children}
    </div>
  );
};
