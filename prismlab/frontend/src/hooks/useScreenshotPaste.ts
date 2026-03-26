import { useEffect, useCallback } from "react";

/**
 * Global paste listener that detects images in the clipboard.
 * When an image is pasted anywhere on the page, extracts raw base64
 * (without data URL prefix) and mimeType, then calls onPaste.
 * Per D-01: only triggers when clipboard contains an image.
 */
export function useScreenshotPaste(
  onPaste: (imageBase64: string, mimeType: string) => void,
) {
  const stableOnPaste = useCallback(onPaste, [onPaste]);

  useEffect(() => {
    const handler = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (const item of Array.from(items)) {
        if (item.type.startsWith("image/")) {
          const blob = item.getAsFile();
          if (!blob) continue;

          const reader = new FileReader();
          reader.onload = () => {
            const dataUrl = reader.result as string;
            // dataUrl format: "data:image/png;base64,iVBOR..."
            const commaIdx = dataUrl.indexOf(",");
            if (commaIdx === -1) return;

            const header = dataUrl.slice(0, commaIdx);
            const base64 = dataUrl.slice(commaIdx + 1);
            const mimeMatch = header.match(/data:(.*?);/);
            const mimeType = mimeMatch?.[1] ?? "image/png";

            stableOnPaste(base64, mimeType);
          };
          reader.readAsDataURL(blob);
          e.preventDefault();
          break; // Only process the first image item
        }
      }
    };

    document.addEventListener("paste", handler);
    return () => document.removeEventListener("paste", handler);
  }, [stableOnPaste]);
}
