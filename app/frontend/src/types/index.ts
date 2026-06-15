export type ImageStatus = "pending" | "processing" | "classified" | "failed";

export interface Annotation {
  id: number;
  image_id: number;
  tag?: string | null;
  note?: string | null;
  created_at?: string | null;
}

export interface GarmentImage {
  id: number;
  filename: string;
  original_filename?: string | null;
  uploaded_at?: string | null;
  status: ImageStatus;
  error_message?: string | null;

  description?: string | null;
  garment_type?: string | null;
  style?: string | null;
  material?: string | null;
  color_palette?: string | null;
  pattern?: string | null;
  season?: string | null;
  occasion?: string | null;
  consumer_profile?: string | null;
  trend_notes?: string | null;

  location_continent?: string | null;
  location_country?: string | null;
  location_city?: string | null;
  designer?: string | null;
  image_year?: number | null;
  image_month?: number | null;

  annotations?: Annotation[];
}

export interface FilterOption {
  value: string;
  count: number;
}

export type FilterFacets = Record<string, FilterOption[]>;

// Map of facet key -> selected values.
export type ActiveFilters = Record<string, string[]>;

export interface UploadContext {
  location_continent?: string;
  location_country?: string;
  location_city?: string;
  designer?: string;
  image_year?: string;
  image_month?: string;
}
