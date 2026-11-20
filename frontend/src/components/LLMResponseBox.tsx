'use client';

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown, { Components } from 'react-markdown';
import { Place, Recommendation } from '@/types/place';
import { PlacePhoto } from '@/components/PlaceDetails';

interface LLMResponseBoxProps {
  llmResponse: string;
  intro?: string;
  outro?: string;
  query: string;
  places: Place[];
  recommendations: Recommendation[];
}

const markdownComponents: Components = {
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
  h1: ({ children }) => <h1 className="text-2xl font-bold mt-4 mb-2">{children}</h1>,
  h2: ({ children }) => <h2 className="text-xl font-bold mt-3 mb-2">{children}</h2>,
  h3: ({ children }) => <h3 className="text-lg font-semibold mt-2 mb-1">{children}</h3>,
  ul: ({ children }) => <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="ml-4">{children}</li>,
  p: ({ children, ...props }) => (
    <p {...props}>
      {children}
    </p>
  ),
};

function ExpandableText({
  text,
  expanded,
  setExpanded,
}: {
  text: string;
  expanded: boolean;
  setExpanded: (expanded: boolean) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [overflows, setOverflows] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element || expanded) return;
    const measure = () => setOverflows(element.scrollHeight > element.clientHeight + 1);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [text, expanded]);

  return (
    <div className="min-w-0 flex-1">
      <div
        ref={ref}
        className={`text-gray-700 leading-relaxed font-inter [&_p]:mb-3 [&_p:last-child]:mb-0 ${expanded ? '' : 'line-clamp-4'}`}
      >
        <ReactMarkdown components={markdownComponents}>{text}</ReactMarkdown>
      </div>
      {(overflows || expanded) && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="mt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
          aria-expanded={expanded}
        >
          {expanded ? 'See less' : 'See more'}
        </button>
      )}
    </div>
  );
}

function BlurbWithPhoto({ text, place }: { text: string; place: Place }) {
  const textRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    setExpanded(false);
  }, [text]);

  return (
    <div className="mt-3 flex items-start gap-3">
      <PlacePhoto
        urls={place.image_urls}
        name={place.name}
        href={place.maps_url}
        fitTo={textRef}
        scale={1.75}
        holdSize={expanded}
      />
      <div ref={textRef} className="min-w-0 flex-1">
        <ExpandableText text={text} expanded={expanded} setExpanded={setExpanded} />
      </div>
    </div>
  );
}

export default function LLMResponseBox({
  llmResponse,
  intro,
  outro,
  query,
  places,
  recommendations,
}: LLMResponseBoxProps) {
  const [displayedText, setDisplayedText] = useState('');
  const structured = recommendations.length > 0;

  useEffect(() => {
    if (!llmResponse || structured) {
      setDisplayedText('');
      return;
    }

    setDisplayedText('');

    let index = 0;
    const interval = setInterval(() => {
      if (index < llmResponse.length) {
        setDisplayedText(llmResponse.slice(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 20);

    return () => clearInterval(interval);
  }, [llmResponse, structured]);

  if (!llmResponse && recommendations.length === 0) return null;

  const placesById = new Map(places.map((place) => [place.place_id, place]));
  const rankById = new Map(places.map((place, index) => [place.place_id, index + 1]));
  const picks = recommendations
    .map((pick) => {
      const place = placesById.get(pick.place_id);
      return place ? { pick, place } : null;
    })
    .filter((item): item is { pick: Recommendation; place: Place } => item !== null);

  return (
    <div className="mb-8 animate-in fade-in duration-500">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Top Choices
        </h3>
        {structured ? (
          <div className="space-y-6">
            <div className="text-gray-700 leading-relaxed font-inter">
              <ReactMarkdown components={markdownComponents}>
                {intro || "I think you'd like the following:"}
              </ReactMarkdown>
            </div>
            {picks.map(({ pick, place }) => (
              <section key={place.place_id} className="border-t border-gray-200 pt-5">
                <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                  <h4 className="text-lg font-bold text-gray-900">
                    {rankById.get(place.place_id)}. {place.name}
                  </h4>
                  {place.neighborhood && (
                    <span className="text-sm text-gray-500">{place.neighborhood}</span>
                  )}
                </div>
                <BlurbWithPhoto text={pick.blurb} place={place} />
                {place.maps_url && (
                  <a
                    href={place.maps_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 inline-block text-sm font-medium text-gray-900 underline underline-offset-2"
                  >
                    {place.name} on Google Maps
                  </a>
                )}
              </section>
            ))}
            {outro && (
              <div className="border-t border-gray-200 pt-5 text-gray-700 leading-relaxed font-inter [&_p]:mb-3 [&_p:last-child]:mb-0">
                <ReactMarkdown components={markdownComponents}>{outro}</ReactMarkdown>
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-700 leading-relaxed text-justify font-inter [&_p]:mb-4 [&_p:last-child]:mb-0">
            <ReactMarkdown components={markdownComponents}>
              {displayedText}
            </ReactMarkdown>
          </div>
        )}
        <div className="text-sm text-gray-500">
          Based on your search for &quot;{query}&quot;
        </div>
      </div>
    </div>
  );
}
