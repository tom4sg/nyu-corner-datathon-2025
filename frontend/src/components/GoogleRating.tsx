interface GoogleRatingProps {
  rating?: number;
  count?: number;
}

export default function GoogleRating({ rating, count }: GoogleRatingProps) {
  if (typeof rating !== 'number') return null;
  const reviews = typeof count === 'number' ? `${count.toLocaleString()} Google reviews` : 'Google reviews';
  return (
    <span className="inline-flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400" aria-label={`${rating.toFixed(1)} stars, ${reviews}`}>
      <span className="font-medium text-gray-900 dark:text-gray-100">{rating.toFixed(1)}</span>
      <svg viewBox="0 0 12 12" aria-hidden className="h-3 w-3 fill-current text-gray-900 dark:text-gray-100">
        <path d="M6 1.1 7.35 4.2l3.35.3-2.55 2.15.78 3.25L6 8.25 3.07 9.9l.78-3.25L1.3 4.5l3.35-.3L6 1.1Z" />
      </svg>
      {typeof count === 'number' && <span>{count.toLocaleString()}</span>}
    </span>
  );
}
