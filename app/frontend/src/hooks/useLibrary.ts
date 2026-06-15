import { useCallback, useEffect, useRef, useState } from "react";
import { fetchFilters, fetchImages } from "../services/api";
import type { ActiveFilters, FilterFacets, GarmentImage } from "../types";

/**
 * Owns the image library state: the active filters, search query, the resulting
 * images, and the dynamically-generated filter facets. Polls while any image is
 * still being classified so freshly-uploaded items light up automatically.
 */
export function useLibrary() {
  const [images, setImages] = useState<GarmentImage[]>([]);
  const [facets, setFacets] = useState<FilterFacets>({});
  const [filters, setFilters] = useState<ActiveFilters>({});
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const timer = useRef<number | null>(null);

  const refresh = useCallback(async () => {
    const [imgs, fac] = await Promise.all([
      fetchImages(filters, query),
      fetchFilters(),
    ]);
    setImages(imgs);
    setFacets(fac);
    setLoading(false);
    return imgs;
  }, [filters, query]);

  // Re-fetch whenever filters or query change.
  useEffect(() => {
    setLoading(true);
    refresh();
  }, [refresh]);

  // Poll while anything is pending/processing.
  useEffect(() => {
    const anyPending = images.some(
      (i) => i.status === "pending" || i.status === "processing"
    );
    if (timer.current) window.clearTimeout(timer.current);
    if (anyPending) {
      timer.current = window.setTimeout(() => refresh(), 2500);
    }
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [images, refresh]);

  const toggleFilter = useCallback((key: string, value: string) => {
    setFilters((prev) => {
      const current = prev[key] || [];
      const next = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      const updated = { ...prev, [key]: next };
      if (next.length === 0) delete updated[key];
      return updated;
    });
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
    setQuery("");
  }, []);

  const activeCount = Object.values(filters).reduce((n, v) => n + v.length, 0);

  return {
    images,
    facets,
    filters,
    query,
    loading,
    activeCount,
    setQuery,
    toggleFilter,
    clearFilters,
    refresh,
  };
}
