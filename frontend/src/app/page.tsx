'use client';

import { useState } from 'react';
import SearchBox from '@/components/SearchBox';
import ResultsList from '@/components/ResultsList';
import LLMResponseBox from '@/components/LLMResponseBox';
import { Place } from '@/types/place';

export default function Home() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [llmResponse, setLlmResponse] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');

  const handleSearch = async (searchQuery: string) => {
    setLoading(true);
    setError(null);
    setQuery(searchQuery);

    try {
      // API URL must be set in production
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error('API URL not configured. Please set NEXT_PUBLIC_API_URL environment variable.');
      }
      
      const response = await fetch(`${apiUrl}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: searchQuery }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setPlaces(data.places || []);
      setLlmResponse(data.llm_response || '');
    } catch (err) {
      setError('Failed to search. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Vibio 
          </h1>
          <p className="text-xl text-gray-600">
            Find the best NYC restaurants and bars
          </p>
        </div>

        {/* Search Section */}
        <div className="max-w-4xl mx-auto">
          <SearchBox onSearch={handleSearch} loading={loading} />
          
          {/* Error Message */}
          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Results */}
          {places.length > 0 && (
            <div className="mt-8">
              {/* LLM Response */}
              <LLMResponseBox llmResponse={llmResponse} query={query} />
              
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-semibold text-gray-900">
                  Search Results
                </h2>
                <span className="text-gray-600">
                  {places.length} places found
                </span>
              </div>
              <ResultsList places={places} />
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="mt-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
              <p className="mt-2 text-gray-600">Searching for the perfect spots...</p>
            </div>
          )}

          {/* Empty State */}
          {!loading && places.length === 0 && query && !error && (
            <div className="mt-8 text-center">
              <p className="text-gray-600 text-lg">
                No places found for &quot;{query}&quot;. Try a different search term!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
