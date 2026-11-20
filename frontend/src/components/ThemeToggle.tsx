export default function ThemeToggle() {
  const toggle = () => {
    const next = !document.documentElement.classList.contains('dark');
    document.documentElement.classList.toggle('dark', next);
    try {
      localStorage.setItem('vibio-theme', next ? 'dark' : 'light');
    } catch {
      // The page still switches for this visit.
    }
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Switch color theme"
      className="fixed right-4 top-3.5 z-30 flex h-9 w-9 items-center justify-center rounded-full text-gray-500 transition-colors hover:bg-black/[0.04] hover:text-gray-900 dark:text-gray-400 dark:hover:bg-white/[0.06] dark:hover:text-gray-100"
    >
      <svg aria-hidden className="h-4 w-4 dark:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.75}
          d="M21 14.5A8.5 8.5 0 1110.5 3 7 7 0 0021 14.5z"
        />
      </svg>
      <svg aria-hidden className="hidden h-4 w-4 dark:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="3.25" strokeWidth={1.75} />
        <path
          strokeLinecap="round"
          strokeWidth={1.75}
          d="M12 3v1.5M12 19.5V21M3 12h1.5M19.5 12H21M5.6 5.6l1.1 1.1M17.3 17.3l1.1 1.1M18.4 5.6l-1.1 1.1M6.7 17.3l-1.1 1.1"
        />
      </svg>
    </button>
  );
}
