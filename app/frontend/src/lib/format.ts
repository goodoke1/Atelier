// Human-friendly facet labels for the dynamically-discovered attribute keys.
const LABELS: Record<string, string> = {
  garment_type: "Garment",
  style: "Style",
  material: "Material",
  color_palette: "Colour",
  pattern: "Pattern",
  season: "Season",
  occasion: "Occasion",
  consumer_profile: "Consumer",
  trend_notes: "Trend",
  location_continent: "Continent",
  location_country: "Country",
  location_city: "City",
  designer: "Designer",
  image_year: "Year",
  image_month: "Month",
};

export const facetLabel = (key: string): string =>
  LABELS[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

const MONTHS = [
  "",
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export function formatLocation(img: {
  location_city?: string | null;
  location_country?: string | null;
  location_continent?: string | null;
}): string | null {
  const parts = [img.location_city, img.location_country, img.location_continent].filter(
    Boolean
  ) as string[];
  return parts.length ? parts.join(", ") : null;
}

export function formatWhen(img: {
  image_month?: number | null;
  image_year?: number | null;
}): string | null {
  const month = img.image_month ? MONTHS[img.image_month] : null;
  if (month && img.image_year) return `${month} ${img.image_year}`;
  if (img.image_year) return `${img.image_year}`;
  return null;
}

export const splitList = (value?: string | null): string[] =>
  (value || "")
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean);
