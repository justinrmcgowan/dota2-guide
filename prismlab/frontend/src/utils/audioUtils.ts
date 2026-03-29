/**
 * audioUtils.ts — TTS utilities for Prismlab audio coaching system.
 *
 * Three exports:
 *   sanitizeForSpeech() — strips visual-only notation before speaking
 *   humanizeItemName()  — converts snake_case item keys to Title Case for speech
 *   speak()             — wraps SpeechSynthesis with Chrome keepalive workaround
 */

/**
 * Strips dash-dash separators, clock notation, and converts gold shorthand
 * to natural language before passing text to the TTS engine.
 *
 * Examples:
 *   "Buy Boots -- early pressure" → "Buy Boots, early pressure"
 *   "Power Treads (12:30)" → "Power Treads"
 *   "You need +2000g" → "You need 2000 gold"
 */
export function sanitizeForSpeech(msg: string): string {
  return msg
    .replace(/--/g, ",")
    .replace(/\(\d+:\d+\)/g, "")
    .replace(/\+(\d+)g/, "$1 gold")
    .trim();
}

/**
 * Converts a snake_case item name to Title Case for natural speech output.
 *
 * Examples:
 *   "blade_mail"     → "Blade Mail"
 *   "black_king_bar" → "Black King Bar"
 */
export function humanizeItemName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Speaks text via the Web Speech API with:
 *   - Silent degradation when SpeechSynthesis is unavailable
 *   - Cancel-before-speak to prevent queue buildup
 *   - Chrome 15-second keepalive via pause/resume interval
 *   - rate=1.1 for a slightly urgent, coach-like cadence
 *
 * @param text   The text to speak (should already be sanitized).
 * @param volume Speaker volume 0.0–1.0.
 */
export function speak(text: string, volume: number): void {
  if (!("speechSynthesis" in window)) return;

  // Cancel any pending speech to avoid queue buildup
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.volume = volume;
  utterance.rate = 1.1;
  utterance.pitch = 1.0;
  // Do NOT set utterance.voice — avoids getVoices() async race condition

  // Chrome 15-second keepalive: Chrome pauses long utterances silently.
  // Calling pause() then resume() every 10s keeps it alive.
  let keepaliveTimer: ReturnType<typeof setInterval> | null = null;

  utterance.onstart = () => {
    keepaliveTimer = setInterval(() => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.pause();
        window.speechSynthesis.resume();
      } else {
        if (keepaliveTimer !== null) clearInterval(keepaliveTimer);
      }
    }, 10_000);
  };

  utterance.onend = () => {
    if (keepaliveTimer !== null) {
      clearInterval(keepaliveTimer);
      keepaliveTimer = null;
    }
  };

  utterance.onerror = () => {
    if (keepaliveTimer !== null) {
      clearInterval(keepaliveTimer);
      keepaliveTimer = null;
    }
  };

  window.speechSynthesis.speak(utterance);
}
