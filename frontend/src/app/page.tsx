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
      <div className="max-w-3xl mx-auto px-4 pt-10 pb-20">
        {/* Header */}
        <div className="text-center mb-12 space-y-4">
          <div className="flex items-center justify-center gap-3 mb-4 w-full">
            <h1 className="text-4xl font-bold text-gray-900 text-center tracking-tight">
              Vibio 
            </h1>
            <img 
              src="/vibio_pin_128x128.png" 
              alt="Vibio Icon" 
              className="w-12 h-12 object-contain"
            />
          </div>
          <p className="text-xl text-gray-600">
            Find the best NYC restaurants and venues
          </p>
        </div>

        {/* Search Section */}
        <div className="space-y-8">
          <SearchBox onSearch={handleSearch} loading={loading} />
          
          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Results */}
          {places.length > 0 && (
            <div className="space-y-8">
              {/* LLM Response */}
              <LLMResponseBox 
                llmResponse={llmResponse} 
                query={query} 
              />
              
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Search Results
                  </h2>
                  <span className="text-gray-600">
                    {places.length} places found
                  </span>
                </div>
                <ResultsList places={places} />
              </div>
            </div>
          )}

          {/* Loading Message */}
          {loading && (
            <div className="mb-6 animate-in fade-in duration-500">
              <div className="text-sm text-gray-500">
                Performing deep search across thousands of venues
                <span className="inline-block dot-pulse" style={{ animationDelay: '0.2s' }}>.</span>
                <span className="inline-block dot-pulse" style={{ animationDelay: '0.4s' }}>.</span>
                <span className="inline-block dot-pulse" style={{ animationDelay: '0.6s' }}>.</span>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!loading && places.length === 0 && query && !error && (
            <div className="text-center">
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
