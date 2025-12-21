import { useCallback, useRef, useMemo, type DragEvent, type ChangeEvent } from 'react';
import {
  Upload,
  FileText,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Trash2,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { UploadedFile, TokenUsage } from '../types/chat';

interface DashboardProps {
  uploadedFiles: UploadedFile[];
  tokenUsage: TokenUsage[];
  onUpload: (file: File) => Promise<void>;
  onDeleteFile: (fileId: string) => void;
  isConnected: boolean;
}

export function Dashboard({
  uploadedFiles,
  tokenUsage,
  onUpload,
  onDeleteFile,
}: DashboardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const tokenStats = useMemo(() => {
    const totalPrompt = tokenUsage.reduce((sum, t) => sum + t.prompt, 0);
    const totalCompletion = tokenUsage.reduce((sum, t) => sum + t.completion, 0);
    return {
      total: totalPrompt + totalCompletion,
      prompt: totalPrompt,
      completion: totalCompletion,
    };
  }, [tokenUsage]);

  const handleDrop = useCallback(
    async (e: DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files?.[0];
      if (file) await onUpload(file);
    },
    [onUpload]
  );

  const handleFileChange = useCallback(
    async (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) await onUpload(file);
      if (fileInputRef.current) fileInputRef.current.value = '';
    },
    [onUpload]
  );

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'ready':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusText = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return 'Uploading...';
      case 'processing':
        return 'Processing...';
      case 'ready':
        return 'Ready';
      case 'error':
        return 'Error';
    }
  };

  return (
    <div className="h-full flex flex-col p-4 pr-2 overflow-hidden">
      {/* RAG Knowledge Base Section */}
      <div className="bg-white rounded-2xl shadow-sm p-4 mb-4 flex-shrink-0">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">
            RAG Knowledge Base
          </h2>
          <span className="text-sm text-gray-500">
            {uploadedFiles.filter((f) => f.status === 'ready').length} documents ready
          </span>
        </div>

        {/* Upload Zone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-gray-200 rounded-xl p-3 text-center cursor-pointer hover:border-blue-300 hover:bg-blue-50/30 transition-colors mb-3"
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.txt,.md,.docx,.xlsx,.json"
            className="hidden"
          />
          <div className="flex items-center justify-center gap-3">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <Upload className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-700">
                Drag & drop or click to upload
              </p>
              <p className="text-xs text-gray-400">
                PDF, TXT, MD, DOCX, XLSX, JSON (max 3 pages for PDF)
              </p>
            </div>
          </div>
        </div>

        {/* File List */}
        <div className="h-28 overflow-y-auto">
          {uploadedFiles.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <FileText className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm">No documents uploaded yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {uploadedFiles.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center shadow-sm">
                      <FileText className="w-4 h-4 text-blue-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800 truncate max-w-[180px]">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-400">
                        {formatFileSize(file.size)} &bull; {file.chunks} chunks
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      {getStatusIcon(file.status)}
                      <span
                        className={`text-xs ${
                          file.status === 'ready'
                            ? 'text-green-600'
                            : file.status === 'error'
                            ? 'text-red-600'
                            : 'text-blue-600'
                        }`}
                      >
                        {getStatusText(file.status)}
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteFile(file.id);
                      }}
                      className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-red-100 rounded-lg transition-all"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Token Usage Section */}
      <div className="bg-white rounded-2xl shadow-sm p-4 flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">
            Token Usage
          </h2>
        </div>

        {/* Token Stats Cards */}
        <div className="grid grid-cols-3 gap-2 mb-3 flex-shrink-0">
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-medium text-gray-500">Total</span>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {tokenStats.total.toLocaleString()}
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              <ArrowUpRight className="w-4 h-4 text-blue-500" />
              <span className="text-xs font-medium text-blue-600">Input</span>
            </div>
            <div className="text-xl font-bold text-blue-600">
              {tokenStats.prompt.toLocaleString()}
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              <ArrowDownRight className="w-4 h-4 text-purple-500" />
              <span className="text-xs font-medium text-purple-600">Output</span>
            </div>
            <div className="text-xl font-bold text-purple-600">
              {tokenStats.completion.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="flex-1 min-h-0">
          {tokenUsage.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400 bg-gray-50 rounded-xl">
              <Zap className="w-10 h-10 mb-2 opacity-30" />
              <p className="text-sm">No usage data yet</p>
              <p className="text-xs mt-1">Start chatting to see token usage</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tokenUsage} barSize={20}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="timestamp"
                  tick={{ fontSize: 10, fill: '#9ca3af' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#9ca3af' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                  width={40}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: 'none',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    fontSize: '12px',
                  }}
                />
                <Bar
                  dataKey="prompt"
                  name="Input"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="completion"
                  name="Output"
                  fill="#a78bfa"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-2 pt-2 border-t border-gray-100 flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-blue-500" />
            <span className="text-xs text-gray-600">Input Tokens</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-purple-400" />
            <span className="text-xs text-gray-600">Output Tokens</span>
          </div>
        </div>
      </div>
    </div>
  );
}
