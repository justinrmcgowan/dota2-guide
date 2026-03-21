import { useState, useEffect } from "react";
import type { Hero } from "../types/hero";
import { api } from "../api/client";

export function useHeroes() {
  const [heroes, setHeroes] = useState<Hero[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getHeroes()
      .then((data) => {
        if (!cancelled) {
          setHeroes(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { heroes, loading, error };
}
