'use client';

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown, { Components } from 'react-markdown';
import { Place, Recommendation } from '@/types/place';
import { PlacePhoto } from '@/components/PlaceDetails';
import GoogleRating from '@/components/GoogleRating';

interface LLMResponseBoxProps {
  llmResponse: string;
  opener?: string;
  outro?: string;
  query: string;
  places: Place[];
  recommendations: Recommendation[];
}

const markdownComponents: Components = {
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono dark:bg-white/10">{children}</code>,
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
  complete,
  expanded,
  setExpanded,
}: {
  text: string;
  complete: boolean;
  expanded: boolean;
  setExpanded: (expanded: boolean) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [overflows, setOverflows] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element || expanded || !complete) {
      if (!complete) setOverflows(false);
      return;
    }
    const measure = () => setOverflows(element.scrollHeight > element.clientHeight + 1);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [text, expanded, complete]);

  return (
    <div className="min-w-0 flex-1">
      <div
        ref={ref}
        className={`text-gray-700 leading-relaxed font-inter dark:text-gray-300 [&_p]:mb-3 [&_p:last-child]:mb-0 ${expanded ? '' : 'line-clamp-4'}`}
      >
        <ReactMarkdown components={markdownComponents}>{text || ''}</ReactMarkdown>
      </div>
      {(overflows || expanded) && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="mt-1 text-sm font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          aria-expanded={expanded}
        >
          {expanded ? 'See less' : 'See more'}
        </button>
      )}
    </div>
  );
}

function BlurbWithPhoto({
  text,
  complete,
  place,
}: {
  text: string;
  complete: boolean;
  place: Place;
}) {
  const textRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    setExpanded(false);
  }, [place.place_id]);

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
        <ExpandableText text={text} complete={complete} expanded={expanded} setExpanded={setExpanded} />
      </div>
    </div>
  );
}

const CHARS_PER_SECOND = 115;
const GAP_MS = 180;

function scheduleStart(parts: string[], index: number) {
  let start = 0;
  for (let i = 0; i < index; i++) {
    start += ((parts[i]?.length ?? 0) / CHARS_PER_SECOND) * 1000 + GAP_MS;
  }
  return start;
}

function scheduleEnd(parts: string[]) {
  if (parts.length === 0) return 0;
  const last = parts.length - 1;
  return scheduleStart(parts, last) + ((parts[last]?.length ?? 0) / CHARS_PER_SECOND) * 1000;
}

function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function useArrival(parts: string[]) {
  const key = parts.join('\u0001');
  const partsRef = useRef(parts);
  partsRef.current = parts;
  const [clock, setClock] = useState({ key: '', elapsed: 0, settled: false });

  useEffect(() => {
    const current = partsRef.current;
    if (prefersReducedMotion()) {
      setClock({ key, elapsed: 0, settled: true });
      return;
    }
    setClock({ key, elapsed: 0, settled: false });
    const origin = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const elapsed = now - origin;
      const done = elapsed >= scheduleEnd(current);
      setClock({ key, elapsed, settled: done });
      if (!done) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [key]);

  const active = clock.key === key ? clock : { elapsed: 0, settled: false };
  const sliceAt = (index: number) => {
    const part = parts[index] ?? '';
    if (active.settled) return part;
    const start = scheduleStart(parts, index);
    if (active.elapsed < start) return null;
    const count = Math.min(part.length, Math.floor(((active.elapsed - start) / 1000) * CHARS_PER_SECOND));
    return part.slice(0, count);
  };

  return { sliceAt, settled: active.settled };
}

export default function LLMResponseBox({
  llmResponse,
  opener,
  outro,
  query,
  places,
  recommendations,
}: LLMResponseBoxProps) {
  const structured = recommendations.length > 0;
  const placesById = new Map(places.map((place) => [place.place_id, place]));
  const picks = recommendations
    .map((pick) => {
      const place = placesById.get(pick.place_id);
      return place ? { pick, place } : null;
    })
    .filter((item): item is { pick: Recommendation; place: Place } => item !== null);

  const opening = opener || "I think you'd like the following:";
  const parts = structured
    ? [opening, ...picks.map(({ pick }) => pick.blurb), ...(outro ? [outro] : [])]
    : [llmResponse];
  const { sliceAt } = useArrival(parts);
  const outroIndex = outro ? parts.length - 1 : -1;

  if (!llmResponse && picks.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Top Choices
        </h3>
        {structured ? (
          <div className="space-y-6">
            <div className="min-h-[1.5em] text-gray-700 leading-relaxed font-inter dark:text-gray-300">
              <ReactMarkdown components={markdownComponents}>
                {sliceAt(0) ?? ''}
              </ReactMarkdown>
            </div>
            {picks.map(({ pick, place }, index) => {
              const shown = sliceAt(index + 1);
              if (shown === null) return null;
              return (
                <section key={place.place_id} className="fade-up border-t border-gray-200 pt-5 dark:border-white/10">
                  <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                    <h4 className="text-lg font-bold text-gray-900 dark:text-gray-100">
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
                    </h4>
                    {place.neighborhood && (
                      <span className="text-sm text-gray-500 dark:text-gray-400">{place.neighborhood}</span>
                    )}
                    <GoogleRating rating={place.google_rating} count={place.google_review_count} />
                  </div>
                  <BlurbWithPhoto text={shown} complete={shown.length === pick.blurb.length} place={place} />
                  {place.maps_url && (
                    <a
                      href={place.maps_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-3 inline-block text-sm font-medium text-gray-900 underline underline-offset-2 dark:text-gray-100"
                    >
                      {place.name} on Google Maps
                    </a>
                  )}
                </section>
              );
            })}
            {outro && sliceAt(outroIndex) !== null && (
              <div className="fade-up border-t border-gray-200 pt-5 text-gray-700 leading-relaxed font-inter dark:border-white/10 dark:text-gray-300 [&_p]:mb-3 [&_p:last-child]:mb-0">
                <ReactMarkdown components={markdownComponents}>{sliceAt(outroIndex) ?? ''}</ReactMarkdown>
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-700 leading-relaxed text-justify font-inter dark:text-gray-300 [&_p]:mb-4 [&_p:last-child]:mb-0">
            <ReactMarkdown components={markdownComponents}>
              {sliceAt(0) ?? ''}
            </ReactMarkdown>
          </div>
        )}
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Based on your search for &quot;{query}&quot;
        </div>
      </div>
    </div>
  );
}
