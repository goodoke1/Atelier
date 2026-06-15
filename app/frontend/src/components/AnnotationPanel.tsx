import { useState } from "react";
import { addAnnotation, deleteAnnotation } from "../services/api";
import type { Annotation } from "../types";

interface Props {
  imageId: number;
  annotations: Annotation[];
  onChange: () => void;
}

/**
 * Designer annotations: human tags + notes, visually distinguished from the
 * AI-generated metadata (accent border + "designer note" label) per the brief.
 */
export default function AnnotationPanel({ imageId, annotations, onChange }: Props) {
  const [tag, setTag] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!tag.trim() && !note.trim()) return;
    setBusy(true);
    await addAnnotation(imageId, { tag: tag.trim(), note: note.trim() });
    setTag("");
    setNote("");
    setBusy(false);
    onChange();
  };

  const remove = async (id: number) => {
    await deleteAnnotation(id);
    onChange();
  };

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <span className="eyebrow text-accent">Designer notes</span>
        <span className="h-px flex-1 bg-accent/30" />
      </div>

      <div className="space-y-2">
        {annotations.length === 0 && (
          <p className="text-sm italic text-muted">
            No notes yet — add your own observations, distinct from the AI reading.
          </p>
        )}
        {annotations.map((a) => (
          <div
            key={a.id}
            className="group rounded-sm border-l-2 border-accent bg-accent/5 px-3 py-2"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                {a.tag && (
                  <span className="mr-2 rounded-full bg-accent px-2 py-0.5 text-[11px] font-medium text-paper">
                    {a.tag}
                  </span>
                )}
                {a.note && <span className="text-sm text-ink">{a.note}</span>}
              </div>
              <button
                onClick={() => remove(a.id)}
                className="text-muted opacity-0 transition group-hover:opacity-100 hover:text-accent"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 space-y-2">
        <input
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          placeholder="Tag (e.g. favourite, rework)"
          className="w-full rounded-sm border border-ink/15 bg-paper px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Observation…"
          rows={2}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
          }}
          className="w-full resize-none rounded-sm border border-ink/15 bg-paper px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <button
          onClick={submit}
          disabled={busy || (!tag.trim() && !note.trim())}
          className="w-full rounded-full bg-accent px-4 py-2 text-sm font-medium text-paper transition enabled:hover:bg-ink disabled:opacity-40"
        >
          Add note
        </button>
      </div>
    </div>
  );
}
