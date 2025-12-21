import { useState, useEffect, useCallback } from 'react';
import { Database, MessageSquare, Search, Bell, Settings } from 'lucide-react';
import { Dashboard } from './components/Dashboard';
import { ChatInterface } from './components/ChatInterface';
import { sendQuery, uploadDocument, checkHealth } from './services/api';
import type { Message, UploadedFile, TokenUsage } from './types/chat';

type MenuType = 'dashboard' | 'chat';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [tokenUsage, setTokenUsage] = useState<TokenUsage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeMenu, setActiveMenu] = useState<MenuType>('dashboard');

  // Health check
  useEffect(() => {
    const checkConnection = async () => {
      const healthy = await checkHealth();
      setIsConnected(healthy);
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle sending message
  const handleSend = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };

    const loadingMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);
    setIsLoading(true);

    try {
      const response = await sendQuery(content);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingMessage.id
            ? { ...msg, content: response.answer, isLoading: false }
            : msg
        )
      );

      // Token usage update
      const now = new Date();
      const timestamp = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      });
      const promptTokens = Math.floor(content.length / 4) + 50;
      const completionTokens = Math.floor(response.answer.length / 4);

      setTokenUsage((prev) => [
        ...prev.slice(-9),
        { timestamp, prompt: promptTokens, completion: completionTokens },
      ]);
    } catch (error) {
      console.error('Query failed:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingMessage.id
            ? { ...msg, content: 'Error: Failed to get response', isLoading: false }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle file upload
  const handleUpload = useCallback(async (file: File) => {
    const fileId = `file-${Date.now()}`;

    const newFile: UploadedFile = {
      id: fileId,
      name: file.name,
      size: file.size,
      chunks: 0,
      status: 'uploading',
      uploadedAt: new Date(),
    };
    setUploadedFiles((prev) => [...prev, newFile]);

    try {
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.id === fileId ? { ...f, status: 'processing' as const } : f
        )
      );

      const response = await uploadDocument(file);

      if (response.success) {
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === fileId
              ? { ...f, chunks: response.data.chunks_created, status: 'ready' as const }
              : f
          )
        );

        const systemMessage: Message = {
          id: `system-${Date.now()}`,
          role: 'assistant',
          content: `**${file.name}** uploaded successfully.\n\n${response.data.chunks_created} chunks created and stored in Qdrant. You can now ask questions about this document.`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, systemMessage]);
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.id === fileId ? { ...f, status: 'error' as const } : f
        )
      );
    }
  }, []);

  const handleDeleteFile = useCallback((fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
  }, []);

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {/* Sidebar */}
      <div className="w-16 bg-white border-r border-gray-200 flex flex-col items-center py-4">
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mb-8">
          <Database className="w-5 h-5 text-white" />
        </div>

        <nav className="flex-1 flex flex-col items-center gap-2">
          <button
            onClick={() => setActiveMenu('dashboard')}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
              activeMenu === 'dashboard'
                ? 'bg-blue-100 text-blue-600'
                : 'text-gray-400 hover:bg-gray-100'
            }`}
            title="Dashboard"
          >
            <Database className="w-5 h-5" />
          </button>
          <button
            onClick={() => setActiveMenu('chat')}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
              activeMenu === 'chat'
                ? 'bg-blue-100 text-blue-600'
                : 'text-gray-400 hover:bg-gray-100'
            }`}
            title="Chat"
          >
            <MessageSquare className="w-5 h-5" />
          </button>
        </nav>

        <div className="flex flex-col items-center gap-2">
          <button className="w-10 h-10 rounded-xl text-gray-400 hover:bg-gray-100 flex items-center justify-center">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-100 border-b border-gray-200">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">RAG Pipeline</h1>
            <p className="text-sm text-gray-500">
              Qdrant Hybrid Search + OpenAI
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 mr-2">
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            <button className="p-2.5 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Search className="w-5 h-5 text-gray-500" />
            </button>
            <button className="p-2.5 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow relative">
              <Bell className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {activeMenu === 'dashboard' && (
            <>
              <div className="w-[40%] flex-shrink-0">
                <Dashboard
                  uploadedFiles={uploadedFiles}
                  tokenUsage={tokenUsage}
                  onUpload={handleUpload}
                  onDeleteFile={handleDeleteFile}
                  isConnected={isConnected}
                />
              </div>
              <div className="w-[60%] h-full flex-shrink-0 p-4 pl-2">
                <ChatInterface
                  messages={messages}
                  onSend={handleSend}
                  isLoading={isLoading}
                  isConnected={isConnected}
                />
              </div>
            </>
          )}

          {activeMenu === 'chat' && (
            <div className="flex-1 p-4">
              <ChatInterface
                messages={messages}
                onSend={handleSend}
                isLoading={isLoading}
                isConnected={isConnected}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
