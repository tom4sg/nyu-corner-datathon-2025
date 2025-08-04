'use client';

import { Place } from '@/types/place';
import { useState, useEffect } from 'react';

interface ResultsListProps {
  places: Place[];
  shouldStartStreaming?: boolean;
}

export default function ResultsList({ places, shouldStartStreaming = false }: ResultsListProps) {
  const [visiblePlaces, setVisiblePlaces] = useState<Place[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    if (places.length > 0 && shouldStartStreaming) {
      setIsStreaming(true);
      setVisiblePlaces([]);
      
      let index = 0;
      const interval = setInterval(() => {
        if (index < places.length) {
          setVisiblePlaces(prev => [...prev, places[index]]);
          index++;
        } else {
          setIsStreaming(false);
          clearInterval(interval);
        }
      }, 300); // Show one result every 300ms

      return () => clearInterval(interval);
    } else if (places.length > 0 && !shouldStartStreaming) {
      // If we have places but shouldn't stream yet, show them all
      setVisiblePlaces(places);
      setIsStreaming(false);
    }
  }, [places, shouldStartStreaming]);

  return (
    <div className="space-y-4">
      {visiblePlaces.map((place, index) => (
        <div
          key={place.place_id}
          className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-1 p-6 border-l-4 border-gray-900 animate-in slide-in-from-bottom-4 fade-in duration-500"
          style={{ animationDelay: `${index * 100}ms` }}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{place.emoji || '📍'}</span>
                <h3 className="text-xl font-semibold text-gray-800">
                  {place.name}
                </h3>
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                  {(place.score * 100).toFixed(0)}% match
                </span>
              </div>
              
              {place.neighborhood && (
                <p className="text-gray-600 font-medium mb-2">
                  📍 {place.neighborhood}
                </p>
              )}
              
              {place.description && (
                <p className="text-gray-600 leading-relaxed mb-3">
                  {place.description}
                </p>
              )}
              
              {place.tags && place.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {place.tags.map((tag, tagIndex) => (
                    <span
                      key={tagIndex}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
            
            <div className="ml-4 text-right">
              <div className="text-sm text-gray-500">
                Rank #{index + 1}
              </div>
            </div>
          </div>
        </div>
      ))}
      
      {isStreaming && (
        <div className="text-center py-4">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
          <p className="mt-2 text-gray-600 text-sm">Loading more results...</p>
        </div>
      )}
    </div>
  );
} 