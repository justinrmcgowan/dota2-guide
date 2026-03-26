import { useState, useEffect, useRef } from "react";
import { useScreenshotStore } from "../../stores/screenshotStore";

interface ItemEditPickerProps {
  heroIdx: number;
  onClose: () => void;
  items: Array<{ name: string; internal_name: string }>;
}

function ItemEditPicker({ heroIdx, onClose, items }: ItemEditPickerProps) {
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const filtered = search.trim()
    ? items
        .filter((item) =>
          item.name.toLowerCase().includes(search.toLowerCase()),
        )
        .slice(0, 8)
    : [];

  const handleSelect = (item: { name: string; internal_name: string }) => {
    useScreenshotStore.getState().addItem(heroIdx, {
      display_name: item.name,
      internal_name: item.internal_name,
      confidence: "high", // User manually added = high confidence
    });
    onClose();
  };

  return (
    <div
      ref={containerRef}
      className="absolute top-full left-0 z-50 mt-1 w-64 bg-bg-secondary border border-bg-elevated rounded-lg shadow-xl overflow-hidden"
    >
      <input
        ref={inputRef}
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search items..."
        className="w-full px-3 py-2 bg-bg-primary border-b border-bg-elevated text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:border-cyan-accent"
      />
      {filtered.length > 0 && (
        <ul className="max-h-48 overflow-y-auto">
          {filtered.map((item) => (
            <li key={item.internal_name}>
              <button
                onClick={() => handleSelect(item)}
                className="w-full px-3 py-1.5 text-left text-sm text-gray-200 hover:bg-bg-elevated transition-colors"
              >
                {item.name}
              </button>
            </li>
          ))}
        </ul>
      )}
      {search.trim() && filtered.length === 0 && (
        <div className="px-3 py-2 text-xs text-gray-500">No items found</div>
      )}
    </div>
  );
}

export default ItemEditPicker;
