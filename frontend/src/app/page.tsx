'use client';

import { MouseEvent, useLayoutEffect, useRef, useState } from 'react';
import Link from 'next/link';
import SearchBox from '@/components/SearchBox';
import ResultsList from '@/components/ResultsList';
import LLMResponseBox from '@/components/LLMResponseBox';
import { INTRO_TEXT, IntroLogo, TYPING_DELAY_MS, Typewriter } from '@/components/Intro';
import { Place, Recommendation } from '@/types/place';
import { nextOpener } from '@/components/openers';
import ThemeToggle from '@/components/ThemeToggle';

const HERO_FADE_MS = 400;
const LEVITATE_MS = 1300;

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export default function Home() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [llmResponse, setLlmResponse] = useState<string>('');
  const [opener, setOpener] = useState('');
  const [outro, setOutro] = useState<string>('');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [resultsOpen, setResultsOpen] = useState(false);
  const [searchMode, setSearchMode] = useState('quick');
  const [moreLoading, setMoreLoading] = useState(false);
  const [moreExhausted, setMoreExhausted] = useState(false);
  const [playIntro, setPlayIntro] = useState(true);
  const [heroLeaving, setHeroLeaving] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const levitateFrom = useRef<number | null>(null);
  const searchGen = useRef(0);

  const searched = query !== '';

  useLayoutEffect(() => {
    const element = searchRef.current;
    const from = levitateFrom.current;
    levitateFrom.current = null;
    if (!searched || !element || from === null) return;

    const distance = from - element.getBoundingClientRect().top;
    element.style.transition = 'none';
    element.style.transform = `translateY(${distance}px)`;
    element.getBoundingClientRect();
    element.style.transition = `transform ${LEVITATE_MS}ms cubic-bezier(0.45, 0, 0.15, 1)`;
    element.style.transform = '';
    const cleanup = () => {
      element.style.transition = '';
    };
    element.addEventListener('transitionend', cleanup, { once: true });
  }, [searched]);

  const handleSearch = async (searchQuery: string, mode: string = 'quick') => {
    if (!searched) {
      setPlayIntro(false);
      if (!reducedMotion()) {
        setHeroLeaving(true);
        await new Promise((resolve) => setTimeout(resolve, HERO_FADE_MS));
        levitateFrom.current = searchRef.current?.getBoundingClientRect().top ?? null;
      }
      setHeroLeaving(false);
    }
    const gen = ++searchGen.current;
    setLoading(true);
    setError(null);
    setQuery(searchQuery);
    setSearchMode(mode);
    setResultsOpen(false);
    setMoreExhausted(false);

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
        body: JSON.stringify({ 
          query: searchQuery,
          mode: mode 
        }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      if (gen !== searchGen.current) return;
      setPlaces(data.places || []);
      setLlmResponse(data.llm_response || '');
      setOpener(nextOpener());
      setOutro(data.outro || '');
      setRecommendations(data.recommendations || []);
    } catch (err) {
      if (gen === searchGen.current) {
        setError('Failed to search. Please try again.');
      }
      console.error('Search error:', err);
    } finally {
      if (gen === searchGen.current) setLoading(false);
    }
  };

  const searchMore = async () => {
    if (moreLoading || moreExhausted || !query) return;
    const gen = searchGen.current;
    setMoreLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error('API URL not configured. Please set NEXT_PUBLIC_API_URL environment variable.');
      }

      const response = await fetch(`${apiUrl}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          mode: searchMode,
          exclude_ids: places.map((place) => place.place_id),
        }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      if (gen !== searchGen.current) return;
      const seen = new Set(places.map((place) => place.place_id));
      const extra = (data.places || []).filter((place: Place) => !seen.has(place.place_id));
      if (extra.length === 0) {
        setMoreExhausted(true);
      } else {
        setPlaces((current) => [...current, ...extra]);
      }
    } catch (err) {
      if (gen === searchGen.current) {
        setError('Failed to search. Please try again.');
      }
      console.error('Search more error:', err);
    } finally {
      if (gen === searchGen.current) setMoreLoading(false);
    }
  };

  const goHome = (event: MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    if (!searched) return;
    setQuery('');
    setPlaces([]);
    setLlmResponse('');
    setOpener('');
    setOutro('');
    setRecommendations([]);
    setError(null);
    setMoreExhausted(false);
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 transition-colors duration-300 dark:bg-[#111113] dark:text-gray-100">
      <ThemeToggle />
      {/* Header: centered hero before searching, compact top bar after */}
      <header
        className={`transition-colors duration-700 ${
          searched
            ? 'sticky top-0 z-20 border-b border-black/[0.06] bg-white/80 backdrop-blur-xl dark:border-white/[0.08] dark:bg-[#111113]/80'
            : 'flex min-h-[88vh] flex-col justify-center border-b border-transparent'
        }`}
      >
        <div
          className={
            searched
              ? 'flex items-center gap-4 py-3 pl-5 pr-16 md:grid md:grid-cols-[1fr_minmax(0,36rem)_1fr] md:pr-5'
              : 'mx-auto flex w-full max-w-xl flex-col items-center gap-12 px-5'
          }
        >
          <Link
            href="/"
            onClick={goHome}
            aria-label="Vibio home"
            className={
              searched
                ? 'fade-up flex shrink-0 items-center gap-1 justify-self-start'
                : `block space-y-5 text-center transition-opacity duration-[400ms] ${heroLeaving ? 'opacity-0' : ''}`
            }
            style={searched ? { animationDelay: `${LEVITATE_MS * 0.6}ms` } : undefined}
          >
            {searched ? (
              <>
                <span className="text-lg font-semibold tracking-[-0.04em] text-gray-900 dark:text-gray-100">Vibio</span>
                <img src="/vibio_pin_128x128.png" alt="" className="h-5 w-5 object-contain dark:invert" />
              </>
            ) : (
              <>
                <IntroLogo />
                <Typewriter text={INTRO_TEXT} animate={playIntro} />
              </>
            )}
          </Link>
          <div
            ref={searchRef}
            className={`w-full min-w-0 flex-1 ${playIntro ? 'fade-up' : ''}`}
            style={playIntro ? { animationDelay: `${TYPING_DELAY_MS + 250}ms` } : undefined}
          >
            <SearchBox onSearch={handleSearch} loading={loading} />
          </div>
        </div>
      </header>

      <div
        className={`max-w-3xl mx-auto px-4 ${searched ? 'fade-up pt-6 pb-20' : ''}`}
        style={searched ? { animationDelay: `${LEVITATE_MS * 0.7}ms` } : undefined}
      >
        <div className="space-y-8">
          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg dark:bg-red-950/40 dark:border-red-900">
              <p className="text-red-700 dark:text-red-300">{error}</p>
            </div>
          )}

          {/* Results */}
          {places.length > 0 && (
            <div className="space-y-8">
              {/* LLM Response */}
              <LLMResponseBox
                llmResponse={llmResponse}
                opener={opener}
                outro={outro}
                query={query}
                places={places}
                recommendations={recommendations}
              />
              
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    <button
                      type="button"
                      onClick={() => setResultsOpen((open) => !open)}
                      aria-expanded={resultsOpen}
                      className="flex items-center gap-2"
                    >
                      <svg
                        aria-hidden
                        className={`h-3.5 w-3.5 text-gray-400 transition-transform duration-200 dark:text-gray-500 ${resultsOpen ? 'rotate-90' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.25} d="M9 5l7 7-7 7" />
                      </svg>
                      All Search Results
                    </button>
                  </h2>
                  <span className="text-gray-600 dark:text-gray-400">
                    {places.length} places found
                  </span>
                </div>
                {resultsOpen && (
                  <>
                    <ResultsList places={places} />
                    <button
                      type="button"
                      onClick={searchMore}
                      disabled={moreLoading || moreExhausted}
                      className="text-sm font-medium text-gray-900 underline-offset-2 hover:underline active:underline disabled:cursor-default disabled:text-gray-400 disabled:no-underline dark:text-gray-100 dark:disabled:text-gray-500"
                    >
                      {moreLoading ? 'Searching…' : moreExhausted ? 'No more places' : 'Search more'}
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* AI Response Loading State */}
          {loading && (
            <div className="mb-6 animate-in fade-in duration-500">
              <h3 className="thinking-shimmer w-fit text-lg font-semibold">
                Top Choices
              </h3>
            </div>
          )}

          {/* Empty State */}
          {!loading && places.length === 0 && query && !error && (
            <div className="text-center">
              <p className="text-gray-600 text-lg dark:text-gray-400">
                No places found for &quot;{query}&quot;. Try a different search term!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
