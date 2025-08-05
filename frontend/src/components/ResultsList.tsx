'use client';

import { Place } from '@/types/place';
import { useState, useEffect } from 'react';

interface ResultsListProps {
  places: Place[];
}

export default function ResultsList({ places }: ResultsListProps) {

  return (
    <div className="space-y-4">
      {places.map((place, index) => (
        <div
          key={place.place_id}
          className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 p-6 animate-in fade-in duration-500"
          style={{ animationDelay: `${index * 100}ms` }}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{place.emoji || '📍'}</span>
                <h3 className="text-xl font-bold text-gray-800">
                  {place.name}
                </h3>
                <span className="text-xs bg-green-100 text-green-800 rounded-full px-2 py-0.5 font-medium">
                  {(place.score * 100).toFixed(0)}% match
                </span>
              </div>
              
              {place.neighborhood && (
                <p className="text-gray-600 font-medium mb-2">
                  📍 {place.neighborhood}
                </p>
              )}
              
              {place.description && (
                <p className="text-gray-600 leading-relaxed mb-3 font-normal font-inter">
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
    </div>
  );
} 