'use client';

import { useState, KeyboardEvent } from 'react';

interface SearchBoxProps {
  onSearch: (query: string) => void;
  loading: boolean;
}

export default function SearchBox({ onSearch, loading }: SearchBoxProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = () => {
    if (query.trim() && !loading) {
      onSearch(query.trim());
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-2xl p-6">
      <div className="flex gap-4">
        <div className="flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search for coffee shops, study spots, restaurants, bars..."
            className="w-full px-4 py-3 text-lg border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none transition-colors"
            disabled={loading}
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={!query.trim() || loading}
          className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-xl hover:from-purple-700 hover:to-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          {loading ? (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Searching...
            </div>
          ) : (
            'Search'
          )}
        </button>
      </div>
      
      {/* Search suggestions */}
      <div className="mt-4 flex flex-wrap gap-2">
        {['coffee shops', 'study spots', 'restaurants', 'bars', 'libraries'].map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => {
              setQuery(suggestion);
              onSearch(suggestion);
            }}
            disabled={loading}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors disabled:opacity-50"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
} 