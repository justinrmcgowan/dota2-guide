import { useEffect } from "react";

interface ErrorBannerProps {
  message: string;
  onDismiss: () => void;
  type: "error" | "fallback";
}

function ErrorBanner({ message, onDismiss, type }: ErrorBannerProps) {
  useEffect(() => {
    if (type !== "error") return;
    const timer = setTimeout(() => {
      onDismiss();
    }, 5000);
    return () => clearTimeout(timer);
  }, [type, onDismiss]);

  if (type === "fallback") {
    return (
      <div className="bg-amber-900/20 border border-amber-500/30 rounded-lg px-4 py-3 mb-4">
        <p className="text-amber-400/80 text-xs">
          AI reasoning unavailable &mdash; showing basic recommendations
        </p>
      </div>
    );
  }

  return (
    <div className="bg-amber-900/30 border border-amber-500/50 rounded-lg px-4 py-3 mb-4 flex items-center justify-between transition-opacity duration-300">
      <p className="text-amber-400 text-sm">{message}</p>
      <button
        onClick={onDismiss}
        className="text-amber-400 hover:text-amber-300 ml-4 shrink-0 transition-colors"
        aria-label="Dismiss error"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    </div>
  );
}

export default ErrorBanner;
