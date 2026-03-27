import { useState, useEffect } from "react";
import { useRefreshStore } from "../../stores/refreshStore";

function AutoRefreshToast() {
  const toast = useRefreshStore((s) => s.lastToast);
  const dismiss = useRefreshStore((s) => s.dismissToast);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!toast) {
      setVisible(false);
      return;
    }
    setVisible(true);
    const timer = setTimeout(() => {
      setVisible(false);
      // Small delay to allow exit animation before clearing state
      setTimeout(() => dismiss(), 300);
    }, 4000);
    return () => clearTimeout(timer);
  }, [toast?.timestamp, dismiss]);

  if (!toast) return null;

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 flex items-start gap-3 bg-surface-container-highest p-4 shadow-glow transition-all duration-300 ${
        visible
          ? "opacity-100 translate-y-0"
          : "opacity-0 translate-y-2 pointer-events-none"
      }`}
    >
      {/* Lightning bolt icon — gold (positive notification) */}
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-secondary mt-0.5 shrink-0"
      >
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
      </svg>
      <div>
        <p className="text-sm font-semibold text-secondary">
          Recommendations updated
        </p>
        <p className="text-xs text-on-surface-variant mt-0.5">{toast.message}</p>
      </div>
    </div>
  );
}

export default AutoRefreshToast;
