import { useEffect, useState } from "react";

interface Props {
  query: string;
  onQuery: (q: string) => void;
  onUpload: () => void;
  count: number;
}

/**
 * Masthead. Editorial title treatment + a debounced natural-language search
 * field ("embroidered neckline", "artisan market") and an upload CTA.
 */
export default function Header({ query, onQuery, onUpload, count }: Props) {
  const [local, setLocal] = useState(query);

  useEffect(() => setLocal(query), [query]);
  useEffect(() => {
    const t = setTimeout(() => onQuery(local), 300);
    return () => clearTimeout(t);
  }, [local, onQuery]);

  return (
    <header className="sticky top-0 z-30 border-b border-ink/10 bg-paper/85 backdrop-blur-md">
      <div className="mx-auto max-w-[1600px] px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-baseline gap-4">
            <h1 className="font-display text-3xl font-black tracking-tight leading-none">
              ATELIER
            </h1>
            <span className="hidden sm:inline eyebrow">
              Inspiration Library · {count} {count === 1 ? "piece" : "pieces"}
            </span>
          </div>

          <div className="flex flex-1 items-center justify-end gap-3 sm:flex-none">
            <div className="relative flex-1 sm:w-80">
              <svg
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
              >
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3-3" />
              </svg>
              <input
                value={local}
                onChange={(e) => setLocal(e.target.value)}
                placeholder="Search the archive…"
                className="w-full rounded-full border border-ink/15 bg-paper py-2 pl-9 pr-4 text-sm outline-none transition focus:border-ink"
              />
            </div>
            <button
              onClick={onUpload}
              className="group inline-flex items-center gap-2 rounded-full bg-ink px-5 py-2 text-sm font-medium text-paper transition hover:bg-accent"
            >
              <svg
                className="h-4 w-4 transition group-hover:rotate-90"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
              >
                <path d="M12 5v14M5 12h14" />
              </svg>
              Capture
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
