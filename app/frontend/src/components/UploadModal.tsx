import { useCallback, useRef, useState } from "react";
import { uploadImage } from "../services/api";
import type { UploadContext } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  onUploaded: () => void;
}

const EMPTY: UploadContext = {
  location_continent: "",
  location_country: "",
  location_city: "",
  designer: "",
  image_year: "",
  image_month: "",
};

export default function UploadModal({ open, onClose, onUploaded }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [context, setContext] = useState<UploadContext>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((list: FileList | null) => {
    if (!list) return;
    const imgs = Array.from(list).filter((f) => f.type.startsWith("image/"));
    setFiles((prev) => [...prev, ...imgs]);
  }, []);

  const reset = () => {
    setFiles([]);
    setContext(EMPTY);
    setBusy(false);
  };

  const submit = async () => {
    if (files.length === 0) return;
    setBusy(true);
    // Upload sequentially so each returns a 202 before we close.
    for (const file of files) {
      try {
        await uploadImage(file, context);
      } catch {
        /* surfaced per-item server-side as failed status */
      }
    }
    onUploaded();
    reset();
    onClose();
  };

  if (!open) return null;

  const field = (
    key: keyof UploadContext,
    label: string,
    type = "text",
    placeholder = ""
  ) => (
    <label className="block">
      <span className="eyebrow">{label}</span>
      <input
        type={type}
        value={context[key]}
        placeholder={placeholder}
        onChange={(e) => setContext((c) => ({ ...c, [key]: e.target.value }))}
        className="mt-1 w-full rounded-sm border border-ink/15 bg-paper px-3 py-2 text-sm outline-none focus:border-ink"
      />
    </label>
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/40 p-4 backdrop-blur-sm sm:p-8"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl animate-fade-up rounded-md bg-paper shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-ink/10 px-6 py-4">
          <div>
            <div className="eyebrow">New entry</div>
            <h2 className="font-display text-2xl">Capture inspiration</h2>
          </div>
          <button
            onClick={onClose}
            className="text-2xl leading-none text-muted hover:text-ink"
          >
            ×
          </button>
        </div>

        <div className="space-y-5 p-6">
          {/* Dropzone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              addFiles(e.dataTransfer.files);
            }}
            onClick={() => inputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed py-10 text-center transition ${
              dragging ? "border-accent bg-accent/5" : "border-ink/20 hover:border-ink"
            }`}
          >
            <svg
              className="mb-2 h-8 w-8 text-muted"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M12 16V4m0 0 4 4m-4-4-4 4" />
              <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
            </svg>
            <p className="font-display text-lg">Drop photos here</p>
            <p className="text-xs text-muted">or click to browse · JPG, PNG, WEBP</p>
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              multiple
              hidden
              onChange={(e) => addFiles(e.target.files)}
            />
          </div>

          {files.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {files.map((f, i) => (
                <span key={i} className="chip">
                  {f.name.length > 22 ? f.name.slice(0, 20) + "…" : f.name}
                  <button
                    onClick={() =>
                      setFiles((prev) => prev.filter((_, idx) => idx !== i))
                    }
                    className="text-muted hover:text-accent"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Context — optional but powers the location & time filters */}
          <div>
            <p className="eyebrow mb-3">
              Context <span className="lowercase tracking-normal">(optional)</span>
            </p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {field("location_continent", "Continent", "text", "Asia")}
              {field("location_country", "Country", "text", "Japan")}
              {field("location_city", "City", "text", "Tokyo")}
              {field("designer", "Designer", "text", "You")}
              {field("image_year", "Year", "number", "2026")}
              {field("image_month", "Month (1–12)", "number", "6")}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-ink/10 px-6 py-4">
          <button
            onClick={onClose}
            className="rounded-full px-4 py-2 text-sm text-muted hover:text-ink"
          >
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={files.length === 0 || busy}
            className="inline-flex items-center gap-2 rounded-full bg-ink px-6 py-2 text-sm font-medium text-paper transition enabled:hover:bg-accent disabled:opacity-40"
          >
            {busy && (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-paper/30 border-t-paper" />
            )}
            {busy ? "Uploading…" : `Classify ${files.length || ""}`.trim()}
          </button>
        </div>
      </div>
    </div>
  );
}
