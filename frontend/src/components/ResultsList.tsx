'use client';

import { MouseEvent } from 'react';
import { Place } from '@/types/place';
import { PlacePhoto } from '@/components/PlaceDetails';

interface ResultsListProps {
  places: Place[];
}

function openPlace(event: MouseEvent, url?: string) {
  if (!url) return;
  const target = event.target as HTMLElement;
  if (target.closest('a, button')) return;
  window.open(url, '_blank', 'noopener,noreferrer');
}

function ReviewSnippet({ snippet, mapsUrl }: { snippet: string; mapsUrl?: string }) {
  return (
    <p className="mt-2 text-sm leading-5 text-gray-600">
      <span className="italic">&ldquo;{snippet}&rdquo;</span>
      {mapsUrl && (
        <>
          {' '}
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-gray-900 hover:underline"
          >
            more
          </a>
        </>
      )}
    </p>
  );
}

function ResultCard({ place, index }: { place: Place; index: number }) {
  return (
    <article
      onClick={(event) => openPlace(event, place.maps_url)}
      className={`bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 p-4 sm:p-6 animate-in fade-in duration-500 ${
        place.maps_url ? 'cursor-pointer' : ''
      }`}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="flex items-start gap-4">
        <PlacePhoto urls={place.image_urls} name={place.name} href={place.maps_url} baseSize={134} />
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-bold text-gray-800">
            {index + 1}.{' '}
            {place.maps_url ? (
              <a
                href={place.maps_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline"
              >
                {place.name}
              </a>
            ) : (
              place.name
            )}
          </h3>

          <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-gray-600">
            {place.neighborhood && (
              <span className="font-medium">{place.neighborhood}</span>
            )}
            {place.neighborhood && place.description && (
              <span aria-hidden className="h-3.5 w-px bg-gray-400" />
            )}
            {place.description && (
              <span className="font-inter">{place.description}</span>
            )}
            {place.tags?.map((tag, tagIndex) => (
              <span
                key={tagIndex}
                className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-full"
              >
                {tag.replaceAll('_', ' ')}
              </span>
            ))}
          </div>

          {place.review_snippet && (
            <ReviewSnippet snippet={place.review_snippet} mapsUrl={place.maps_url} />
          )}
        </div>
      </div>
    </article>
  );
}

export default function ResultsList({ places }: ResultsListProps) {
  return (
    <div className="space-y-4">
      {places.map((place, index) => (
        <ResultCard key={place.place_id} place={place} index={index} />
      ))}
    </div>
  );
}
