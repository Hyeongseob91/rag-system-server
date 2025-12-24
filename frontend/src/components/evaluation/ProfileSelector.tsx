/**
 * ProfileSelector Component
 *
 * 실험 프로파일 선택 드롭다운
 */

import React from 'react';
import { ChevronDown, Check, Zap, Search, Layers } from 'lucide-react';
import type { ProfileInfo } from '../../types/evaluation';

interface ProfileSelectorProps {
  profiles: ProfileInfo[];
  selectedId: string;
  onSelect: (profileId: string) => void;
  isLoading?: boolean;
}

export const ProfileSelector: React.FC<ProfileSelectorProps> = ({
  profiles,
  selectedId,
  onSelect,
  isLoading = false,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  const selectedProfile = profiles.find((p) => p.id === selectedId);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getProfileIcon = (profile: ProfileInfo) => {
    if (profile.id === 'fast') return <Zap className="w-4 h-4" />;
    if (profile.use_reranker) return <Layers className="w-4 h-4" />;
    return <Search className="w-4 h-4" />;
  };

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition-colors disabled:opacity-50"
      >
        {selectedProfile && (
          <>
            <span className="text-gray-600">
              {getProfileIcon(selectedProfile)}
            </span>
            <span className="text-sm font-medium text-gray-700">
              {selectedProfile.name}
            </span>
          </>
        )}
        <ChevronDown
          className={`w-4 h-4 text-gray-400 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-2 w-72 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-2">
            {profiles.map((profile) => (
              <button
                key={profile.id}
                onClick={() => {
                  onSelect(profile.id);
                  setIsOpen(false);
                }}
                className={`w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors ${
                  profile.id === selectedId
                    ? 'bg-blue-50'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div
                  className={`mt-0.5 ${
                    profile.id === selectedId
                      ? 'text-blue-600'
                      : 'text-gray-400'
                  }`}
                >
                  {getProfileIcon(profile)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-sm font-medium ${
                        profile.id === selectedId
                          ? 'text-blue-700'
                          : 'text-gray-700'
                      }`}
                    >
                      {profile.name}
                    </span>
                    {profile.id === selectedId && (
                      <Check className="w-4 h-4 text-blue-600" />
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                    {profile.description}
                  </p>

                  <div className="flex gap-2 mt-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        profile.retriever_type === 'hybrid'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {profile.retriever_type}
                    </span>
                    {profile.use_reranker && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                        reranker
                      </span>
                    )}
                    {profile.use_query_rewrite && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                        query rewrite
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
