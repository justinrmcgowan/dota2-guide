import { useEffect } from "react";

const FALLBACK_MESSAGES: Record<string, string> = {
  timeout:
    "AI timed out \u2014 showing rules-based build. Try again in a moment.",
  parse_error: "AI response was malformed \u2014 showing rules-based build.",
  api_error:
    "AI service unavailable \u2014 showing rules-based build. Try again shortly.",
  rate_limited:
    "AI rate limited \u2014 showing rules-based build. Try again in a moment.",
};

interface ErrorBannerProps {
  message: string;
  onDismiss: () => void;
  type: "error" | "fallback";
  fallbackReason?: string | null;
}

function ErrorBanner({
  message,
  onDismiss,
  type,
  fallbackReason,
}: ErrorBannerProps) {
  useEffect(() => {
    if (type === "error" || type === "fallback") {
      const timer = setTimeout(() => {
        onDismiss();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [type, onDismiss]);

  if (type === "fallback") {
    const displayMessage = fallbackReason
      ? (FALLBACK_MESSAGES[fallbackReason] ??
        "AI reasoning unavailable \u2014 showing basic recommendations")
      : "AI reasoning unavailable \u2014 showing basic recommendations";

    return (
      <div className="bg-secondary/10 border border-outline-variant/15 px-4 py-3 mb-4">
        <p className="text-secondary/80 text-xs">{displayMessage}</p>
      </div>
    );
  }

  return (
    <div className="bg-primary-container/15 border border-outline-variant/15 px-4 py-3 mb-4 flex items-center justify-between transition-opacity duration-300">
      <p className="text-primary text-sm">{message}</p>
      <button
        onClick={onDismiss}
        className="text-primary hover:text-primary/80 ml-4 shrink-0 transition-colors"
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
