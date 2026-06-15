import { imageFileUrl } from "../services/api";
import { formatLocation } from "../lib/format";
import type { GarmentImage } from "../types";

interface Props {
  image: GarmentImage;
  onOpen: (image: GarmentImage) => void;
}

function StatusVeil({ status }: { status: GarmentImage["status"] }) {
  if (status === "classified") return null;
  const label =
    status === "failed" ? "Classification failed" : "Reading the garment…";
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-ink/55 text-paper">
      {status !== "failed" && (
        <span className="h-6 w-6 animate-spin rounded-full border-2 border-paper/30 border-t-paper" />
      )}
      <span className="font-mono text-[10px] uppercase tracking-widest">
        {label}
      </span>
    </div>
  );
}

export default function ImageCard({ image, onOpen }: Props) {
  const location = formatLocation(image);
  const annotated = (image.annotations?.length ?? 0) > 0;

  return (
    <figure
      onClick={() => onOpen(image)}
      className="group relative cursor-pointer overflow-hidden rounded-sm bg-sand shadow-sm ring-1 ring-ink/5 transition duration-300 hover:shadow-xl hover:ring-ink/15 animate-fade-up"
    >
      <div className="relative overflow-hidden">
        <img
          src={imageFileUrl(image.id)}
          alt={image.garment_type || "garment"}
          loading="lazy"
          className="w-full object-cover transition duration-700 ease-out group-hover:scale-[1.04]"
        />
        <StatusVeil status={image.status} />

        {annotated && (
          <span
            className="absolute right-2 top-2 rounded-full bg-paper/90 px-2 py-0.5 font-mono text-[9px] uppercase tracking-widest text-ink"
            title="Has designer notes"
          >
            ✎ noted
          </span>
        )}
      </div>

      {/* Caption slides up on hover — editorial overlay */}
      <figcaption className="pointer-events-none absolute inset-x-0 bottom-0 translate-y-2 bg-gradient-to-t from-ink/90 via-ink/50 to-transparent p-4 pt-10 text-paper opacity-0 transition duration-300 group-hover:translate-y-0 group-hover:opacity-100">
        <div className="font-display text-lg capitalize leading-tight">
          {image.garment_type || "Untitled"}
        </div>
        <div className="mt-0.5 flex flex-wrap items-center gap-x-2 font-mono text-[10px] uppercase tracking-widest text-paper/70">
          {image.style && <span className="capitalize">{image.style}</span>}
          {location && <span>· {location}</span>}
        </div>
      </figcaption>
    </figure>
  );
}
