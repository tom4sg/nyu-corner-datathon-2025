'use client';

import { useState, KeyboardEvent } from 'react';

interface SearchBoxProps {
  onSearch: (query: string, mode: string) => void;
  loading: boolean;
}

export default function SearchBox({ onSearch, loading }: SearchBoxProps) {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState('quick'); // Default to quick search

  const handleSubmit = () => {
    if (query.trim() && !loading) {
      onSearch(query.trim(), searchMode);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="flex gap-1">
      {/* Search Mode Dropdown */}
      <div className="relative">
        <select
          value={searchMode}
          onChange={(e) => setSearchMode(e.target.value)}
          disabled={loading}
          className="h-[52px] px-4 py-3 pr-8 text-sm border-2 border-gray-300 rounded-2xl focus-within:ring-2 ring-gray-400 focus:border-gray-500 focus:outline-none transition-all duration-200 text-gray-900 bg-white shadow-md hover:shadow-lg appearance-none cursor-pointer disabled:opacity-50"
          style={{ minWidth: '140px' }}
        >
          <option value="deep">Advanced Search</option>
          <option value="quick">Quick Search</option>
        </select>
        <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Search Input */}
      <div className="flex-1">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Search places"
          className="w-full h-[52px] px-4 py-3 text-lg border-2 border-gray-300 rounded-2xl focus-within:ring-2 ring-gray-400 focus:border-gray-500 focus:outline-none transition-all duration-200 text-gray-900 shadow-md hover:shadow-lg"
          disabled={loading}
        />
      </div>

      {/* Search Button */}
      <button
        onClick={handleSubmit}
        disabled={!query.trim() || loading}
        className="h-[52px] px-4 py-3 bg-gray-900 text-white rounded-2xl hover:bg-gray-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg transform hover:-translate-y-0.5 flex items-center justify-center"
      >
        {loading ? (
          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17L17 7M17 7H7M17 7V17" />
          </svg>
        )}
      </button>
    </div>
  );
} 
