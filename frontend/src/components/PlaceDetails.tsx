'use client';

import { PointerEvent, RefObject, useEffect, useState } from 'react';

const MIN_SIZE = 64;
const MAX_SIZE = 360;
const DEFAULT_SIZE = 112;

function clampSize(size: number) {
  return Math.round(Math.min(MAX_SIZE, Math.max(MIN_SIZE, size)));
}

export function PlacePhoto({
  urls,
  name,
  href,
  fitTo,
  scale = 1,
  baseSize = DEFAULT_SIZE,
  holdSize = false,
}: {
  urls?: string[];
  name: string;
  href?: string;
  fitTo?: RefObject<HTMLElement | null>;
  scale?: number;
  baseSize?: number;
  holdSize?: boolean;
}) {
  const photos = (urls || []).filter((url) => url.startsWith('https://'));
  const photoKey = photos.join('|');
  const [index, setIndex] = useState(0);
  const [failed, setFailed] = useState(false);
  const [fitSize, setFitSize] = useState<number | null>(null);
  const [dragSize, setDragSize] = useState<number | null>(null);

  useEffect(() => {
    setIndex(0);
    setFailed(false);
  }, [photoKey]);

  useEffect(() => {
    const element = fitTo?.current;
    if (!element || holdSize) return;
    const measure = () => {
      const next = clampSize(element.getBoundingClientRect().height * scale);
      setFitSize((current) => (current !== null && Math.abs(current - next) < 2 ? current : next));
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [fitTo, scale, holdSize]);

  if (!photos.length || failed) return null;

  const src = photos[Math.min(index, photos.length - 1)];
  const size = dragSize ?? fitSize ?? baseSize;

  const startDrag = (event: PointerEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const start = { x: event.clientX, y: event.clientY, size };

    const move = (moveEvent: globalThis.PointerEvent) => {
      const grow = Math.max(moveEvent.clientX - start.x, moveEvent.clientY - start.y);
      setDragSize(clampSize(start.size + grow));
    };
    const stop = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', stop);
      window.removeEventListener('pointercancel', stop);
    };

    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', stop);
    window.addEventListener('pointercancel', stop);
  };

  const image = (
    <img
      src={src}
      alt={name}
      loading="lazy"
      referrerPolicy="no-referrer"
      draggable={false}
      onError={() => {
        if (index < photos.length - 1) {
          setIndex(index + 1);
        } else {
          setFailed(true);
        }
      }}
      style={{ width: size, height: size }}
      className="rounded-lg bg-gray-100 object-cover"
    />
  );

  return (
    <div className="group relative shrink-0">
      {href ? (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Open ${name}`}
          onClick={(event) => event.stopPropagation()}
          className="block"
        >
          {image}
        </a>
      ) : (
        image
      )}
      <button
        type="button"
        aria-label="Resize photo"
        title="Drag to resize, double-click to reset"
        onPointerDown={startDrag}
        onClick={(event) => event.stopPropagation()}
        onDoubleClick={(event) => {
          event.stopPropagation();
          setDragSize(null);
        }}
        className="absolute -bottom-1 -right-1 h-4 w-4 cursor-nwse-resize touch-none rounded-sm border border-gray-300 bg-white/90 opacity-0 shadow-sm transition-opacity group-hover:opacity-100 focus:opacity-100"
      />
    </div>
  );
}
