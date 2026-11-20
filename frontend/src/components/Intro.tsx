'use client';

import { useEffect, useState } from 'react';

export const INTRO_TEXT =
  "Welcome to Vibio. Use this to find the best NYC restaurants and venues that you want but don't know how to describe.";

export const TYPING_DELAY_MS = 500;
const TYPING_SPEED_MS = 20;

function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export function IntroLogo() {
  return (
    <div className="flex items-center justify-center gap-2.5">
      <h1 className="text-[44px] font-semibold leading-none tracking-[-0.04em] text-gray-900">Vibio</h1>
      <img src="/vibio_pin_128x128.png" alt="" className="h-9 w-9 object-contain" />
    </div>
  );
}

export function Typewriter({ text, animate }: { text: string; animate: boolean }) {
  const [count, setCount] = useState(animate ? 0 : text.length);

  useEffect(() => {
    if (!animate || prefersReducedMotion()) {
      setCount(text.length);
      return;
    }
    setCount(0);
    let frame = 0;
    let shown = 0;
    let startedAt: number | null = null;

    const tick = (now: number) => {
      startedAt ??= now;
      const next = Math.min(text.length, Math.floor((now - startedAt) / TYPING_SPEED_MS));
      if (next !== shown) {
        shown = next;
        setCount(next);
      }
      if (next < text.length) frame = requestAnimationFrame(tick);
    };
    const delay = setTimeout(() => {
      frame = requestAnimationFrame(tick);
    }, TYPING_DELAY_MS);

    return () => {
      clearTimeout(delay);
      cancelAnimationFrame(frame);
    };
  }, [text, animate]);

  const typing = animate && count > 0 && count < text.length;

  return (
    <p className="mx-auto max-w-md text-[15px] leading-relaxed text-gray-500" aria-label={text}>
      <span aria-hidden>{text.slice(0, count)}</span>
      <span
        aria-hidden
        className={`relative inline-block h-4 w-0 align-[-2px] transition-opacity duration-500 before:absolute before:-left-px before:top-0 before:h-full before:w-px before:bg-gray-400 ${
          typing ? 'opacity-100' : 'opacity-0'
        }`}
      />
      <span aria-hidden className="text-transparent">{text.slice(count)}</span>
    </p>
  );
}
