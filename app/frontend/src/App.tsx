import { useState } from "react";
import Header from "./components/Header";
import FilterRail from "./components/FilterRail";
import ImageGrid from "./components/ImageGrid";
import ImageDetail from "./components/ImageDetail";
import UploadModal from "./components/UploadModal";
import { facetLabel } from "./lib/format";
import { useLibrary } from "./hooks/useLibrary";
import type { GarmentImage } from "./types";

export default function App() {
  const lib = useLibrary();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selected, setSelected] = useState<GarmentImage | null>(null);

  return (
    <div className="min-h-screen">
      <Header
        query={lib.query}
        onQuery={lib.setQuery}
        onUpload={() => setUploadOpen(true)}
        count={lib.images.length}
      />

      <main className="mx-auto max-w-[1600px] px-6 py-6">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[260px_1fr]">
          {/* Filter rail */}
          <div className="hidden lg:block">
            <FilterRail
              facets={lib.facets}
              filters={lib.filters}
              activeCount={lib.activeCount}
              onToggle={lib.toggleFilter}
              onClear={lib.clearFilters}
            />
          </div>

          {/* Library */}
          <div>
            {/* Active filter / search pills */}
            {(lib.activeCount > 0 || lib.query) && (
              <div className="mb-5 flex flex-wrap items-center gap-2">
                {lib.query && (
                  <span className="chip chip-active">
                    “{lib.query}”
                    <button onClick={() => lib.setQuery("")}>×</button>
                  </span>
                )}
                {Object.entries(lib.filters).flatMap(([key, values]) =>
                  values.map((v) => (
                    <span key={`${key}:${v}`} className="chip chip-active">
                      <span className="text-paper/60">{facetLabel(key)}:</span>
                      <span className="capitalize">{v}</span>
                      <button onClick={() => lib.toggleFilter(key, v)}>×</button>
                    </span>
                  ))
                )}
                <button
                  onClick={lib.clearFilters}
                  className="font-mono text-[11px] uppercase tracking-widest text-accent hover:underline"
                >
                  Reset
                </button>
              </div>
            )}

            <ImageGrid
              images={lib.images}
              loading={lib.loading}
              onOpen={setSelected}
              onUpload={() => setUploadOpen(true)}
            />
          </div>
        </div>
      </main>

      <footer className="mx-auto max-w-[1600px] px-6 pb-10 pt-6">
        <div className="hairline pt-4 font-mono text-[11px] uppercase tracking-widest text-muted">
          Atelier · AI-assisted fashion inspiration archive
        </div>
      </footer>

      {selected && (
        <ImageDetail
          image={selected}
          onClose={() => setSelected(null)}
          onChanged={lib.refresh}
        />
      )}

      <UploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploaded={lib.refresh}
      />
    </div>
  );
}
