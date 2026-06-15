import { useEffect, useState } from "react";
import { deleteImage, fetchImage, imageFileUrl } from "../services/api";
import {
  facetLabel,
  formatLocation,
  formatWhen,
  splitList,
} from "../lib/format";
import type { GarmentImage } from "../types";
import AnnotationPanel from "./AnnotationPanel";

interface Props {
  image: GarmentImage;
  onClose: () => void;
  onChanged: () => void;
}

const ATTRIBUTE_ORDER = [
  "garment_type",
  "style",
  "material",
  "color_palette",
  "pattern",
  "season",
  "occasion",
  "consumer_profile",
  "trend_notes",
];

export default function ImageDetail({ image: initial, onClose, onChanged }: Props) {
  const [image, setImage] = useState<GarmentImage>(initial);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const reload = async () => {
    const fresh = await fetchImage(initial.id);
    setImage(fresh);
    onChanged();
  };

  useEffect(() => {
    setImage(initial);
  }, [initial]);

  // Close on Escape.
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  const handleDelete = async () => {
    await deleteImage(image.id);
    onChanged();
    onClose();
  };

  const location = formatLocation(image);
  const when = formatWhen(image);

  return (
    <div
      className="fixed inset-0 z-40 flex justify-end bg-ink/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="scroll-thin h-full w-full max-w-3xl animate-fade-up overflow-y-auto bg-paper shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Imagery */}
        <div className="relative bg-ink">
          <img
            src={imageFileUrl(image.id)}
            alt={image.garment_type || "garment"}
            className="max-h-[60vh] w-full object-contain"
          />
          <button
            onClick={onClose}
            className="absolute right-4 top-4 flex h-9 w-9 items-center justify-center rounded-full bg-paper/90 text-xl text-ink transition hover:bg-paper"
          >
            ×
          </button>
        </div>

        <div className="px-7 py-6">
          {/* Title block */}
          <div className="flex items-end justify-between gap-4 border-b border-ink/10 pb-4">
            <div>
              <div className="eyebrow">
                {[location, when].filter(Boolean).join(" · ") || "No context recorded"}
              </div>
              <h2 className="mt-1 font-display text-4xl capitalize leading-none">
                {image.garment_type || "Untitled garment"}
              </h2>
              {image.designer && (
                <p className="mt-1 font-display text-sm italic text-muted">
                  Captured by {image.designer}
                </p>
              )}
            </div>
          </div>

          {image.status !== "classified" && (
            <div className="mt-4 rounded-sm bg-sand px-4 py-3 text-sm text-muted">
              {image.status === "failed"
                ? `Classification failed: ${image.error_message || "unknown error"}`
                : "This piece is still being read by the model…"}
            </div>
          )}

          {/* AI description */}
          {image.description && (
            <div className="mt-5">
              <span className="eyebrow">AI reading</span>
              <p className="mt-2 font-display text-lg leading-relaxed text-ink/90">
                {image.description}
              </p>
            </div>
          )}

          {/* Structured attributes */}
          <div className="mt-6 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3">
            {ATTRIBUTE_ORDER.map((key) => {
              const value = (image as unknown as Record<string, unknown>)[
                key
              ] as string | null;
              if (!value) return null;
              return (
                <div key={key}>
                  <div className="eyebrow">{facetLabel(key)}</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {splitList(value).map((part) => (
                      <span
                        key={part}
                        className="rounded-sm bg-sand px-2 py-0.5 text-sm capitalize text-ink"
                      >
                        {part}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Designer annotations */}
          <div className="mt-8 border-t border-ink/10 pt-6">
            <AnnotationPanel
              imageId={image.id}
              annotations={image.annotations || []}
              onChange={reload}
            />
          </div>

          {/* Danger zone */}
          <div className="mt-8 flex items-center justify-between border-t border-ink/10 pt-5">
            <span className="font-mono text-[11px] uppercase tracking-widest text-muted">
              Entry #{image.id}
            </span>
            {confirmDelete ? (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted">Remove permanently?</span>
                <button
                  onClick={handleDelete}
                  className="rounded-full bg-accent px-4 py-1.5 text-paper hover:bg-ink"
                >
                  Delete
                </button>
                <button
                  onClick={() => setConfirmDelete(false)}
                  className="px-2 py-1.5 text-muted hover:text-ink"
                >
                  Keep
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDelete(true)}
                className="font-mono text-[11px] uppercase tracking-widest text-muted hover:text-accent"
              >
                Delete entry
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
