import ImageCard from "./ImageCard";
import type { GarmentImage } from "../types";

interface Props {
  images: GarmentImage[];
  loading: boolean;
  onOpen: (image: GarmentImage) => void;
  onUpload: () => void;
}

function Skeletons() {
  const heights = [260, 340, 300, 380, 290, 360, 320, 280];
  return (
    <div className="masonry">
      {heights.map((h, i) => (
        <div
          key={i}
          className="skeleton rounded-sm"
          style={{ height: h }}
        />
      ))}
    </div>
  );
}

function EmptyState({ onUpload }: { onUpload: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-sm border border-dashed border-ink/20 py-24 text-center">
      <div className="font-display text-5xl italic text-ink/20">∅</div>
      <h3 className="mt-4 font-display text-2xl">Nothing in the archive yet</h3>
      <p className="mt-2 max-w-sm text-sm text-muted">
        Capture inspiration from the field and the model will catalogue garment
        type, style, material, palette, mood, and context for you.
      </p>
      <button
        onClick={onUpload}
        className="mt-6 rounded-full bg-ink px-6 py-2.5 text-sm font-medium text-paper transition hover:bg-accent"
      >
        Capture your first piece
      </button>
    </div>
  );
}

export default function ImageGrid({ images, loading, onOpen, onUpload }: Props) {
  if (loading) return <Skeletons />;
  if (images.length === 0) return <EmptyState onUpload={onUpload} />;

  return (
    <div className="masonry">
      {images.map((img) => (
        <ImageCard key={img.id} image={img} onOpen={onOpen} />
      ))}
    </div>
  );
}
