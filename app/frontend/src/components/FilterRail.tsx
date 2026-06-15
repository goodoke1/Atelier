import { useState } from "react";
import { facetLabel } from "../lib/format";
import type { ActiveFilters, FilterFacets } from "../types";

interface Props {
  facets: FilterFacets;
  filters: ActiveFilters;
  activeCount: number;
  onToggle: (key: string, value: string) => void;
  onClear: () => void;
}

// Group facets into editorial sections so the rail reads like a contents page.
const SECTIONS: { title: string; keys: string[] }[] = [
  {
    title: "Garment",
    keys: ["garment_type", "style", "material", "pattern", "color_palette"],
  },
  { title: "Mood", keys: ["season", "occasion", "consumer_profile", "trend_notes"] },
  {
    title: "Context",
    keys: [
      "location_continent",
      "location_country",
      "location_city",
      "designer",
      "image_year",
      "image_month",
    ],
  },
];

function Facet({
  facetKey,
  options,
  selected,
  onToggle,
}: {
  facetKey: string;
  options: { value: string; count: number }[];
  selected: string[];
  onToggle: (key: string, value: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? options : options.slice(0, 6);
  return (
    <div className="py-3">
      <div className="eyebrow mb-2">{facetLabel(facetKey)}</div>
      <div className="flex flex-wrap gap-1.5">
        {visible.map((opt) => {
          const active = selected.includes(opt.value);
          return (
            <button
              key={opt.value}
              onClick={() => onToggle(facetKey, opt.value)}
              className={`chip ${active ? "chip-active" : "hover:border-ink"}`}
              title={`${opt.count} item${opt.count === 1 ? "" : "s"}`}
            >
              <span className="capitalize">{opt.value}</span>
              <span className={active ? "text-paper/60" : "text-muted/70"}>
                {opt.count}
              </span>
            </button>
          );
        })}
        {options.length > 6 && (
          <button
            onClick={() => setExpanded((e) => !e)}
            className="chip border-dashed text-muted hover:border-ink"
          >
            {expanded ? "less" : `+${options.length - 6}`}
          </button>
        )}
      </div>
    </div>
  );
}

export default function FilterRail({
  facets,
  filters,
  activeCount,
  onToggle,
  onClear,
}: Props) {
  return (
    <aside className="scroll-thin h-[calc(100vh-5rem)] overflow-y-auto pr-2">
      <div className="flex items-center justify-between pb-2">
        <h2 className="font-display text-xl">Refine</h2>
        {activeCount > 0 && (
          <button
            onClick={onClear}
            className="font-mono text-[11px] uppercase tracking-widest text-accent hover:underline"
          >
            Clear ({activeCount})
          </button>
        )}
      </div>

      {SECTIONS.map((section) => {
        const present = section.keys.filter(
          (k) => facets[k] && facets[k].length > 0
        );
        if (present.length === 0) return null;
        return (
          <section key={section.title} className="border-t border-ink/10 pt-2">
            <h3 className="mt-2 font-display text-sm italic text-muted">
              {section.title}
            </h3>
            {present.map((key) => (
              <Facet
                key={key}
                facetKey={key}
                options={facets[key]}
                selected={filters[key] || []}
                onToggle={onToggle}
              />
            ))}
          </section>
        );
      })}

      {Object.keys(facets).length === 0 && (
        <p className="py-6 text-sm text-muted">
          Filters appear here once images are classified.
        </p>
      )}
    </aside>
  );
}
