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

  const canSubmit = Boolean(query.trim()) && !loading;

  return (
    <div className="flex h-12 items-center rounded-full border border-black/[0.08] bg-white pl-4 pr-1.5 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_12px_32px_-16px_rgba(0,0,0,0.18)] transition-[box-shadow,border-color,background-color] duration-300 focus-within:border-black/[0.14] focus-within:shadow-[0_1px_2px_rgba(0,0,0,0.05),0_16px_40px_-16px_rgba(0,0,0,0.26)] dark:border-white/[0.1] dark:bg-[#1c1c1e] dark:shadow-none dark:focus-within:border-white/[0.18]">
      <svg aria-hidden className="h-4 w-4 shrink-0 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="7" strokeWidth={1.75} />
        <path strokeLinecap="round" strokeWidth={1.75} d="M20 20l-3.5-3.5" />
      </svg>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Describe a vibe"
        aria-label="Search places"
        className="h-full min-w-0 flex-1 bg-transparent px-3 text-[15px] text-gray-900 placeholder:text-gray-400 focus:outline-none dark:text-gray-100 dark:placeholder:text-gray-500"
        disabled={loading}
      />

      <div className="relative shrink-0">
        <select
          aria-label="Search mode"
          value={searchMode}
          onChange={(e) => setSearchMode(e.target.value)}
          disabled={loading}
          className="cursor-pointer appearance-none rounded-full bg-transparent py-1.5 pl-3 pr-6 text-xs text-gray-400 transition-colors hover:text-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-200 disabled:opacity-50 dark:hover:text-gray-200 dark:focus-visible:ring-white/20"
        >
          <option value="quick">Quick</option>
          <option value="deep">Advanced</option>
        </select>
        <svg
          aria-hidden
          className="pointer-events-none absolute right-2 top-1/2 h-2.5 w-2.5 -translate-y-1/2 text-gray-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      <button
        type="button"
        aria-label="Search"
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={`ml-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-all duration-300 ${
          canSubmit || loading
            ? 'bg-gray-900 text-white hover:bg-gray-700 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-white'
            : 'bg-gray-100 text-gray-400 dark:bg-white/10 dark:text-gray-500'
        } disabled:cursor-default`}
      >
        {loading ? (
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-[1.5px] border-white border-t-transparent dark:border-gray-900 dark:border-t-transparent" />
        ) : (
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        )}
      </button>
    </div>
  );
}
