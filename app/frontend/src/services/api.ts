import axios from "axios";
import type {
  ActiveFilters,
  Annotation,
  FilterFacets,
  GarmentImage,
  UploadContext,
} from "../types";

const client = axios.create({ baseURL: "/api" });

export const imageFileUrl = (id: number) => `/api/images/${id}/file`;

function filtersToParams(filters: ActiveFilters, q?: string): URLSearchParams {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, values]) => {
    values.forEach((v) => params.append(key, v));
  });
  if (q && q.trim()) params.set("q", q.trim());
  return params;
}

export async function fetchImages(
  filters: ActiveFilters = {},
  q?: string
): Promise<GarmentImage[]> {
  const params = filtersToParams(filters, q);
  const { data } = await client.get(`/images?${params.toString()}`);
  return data.images as GarmentImage[];
}

export async function fetchImage(id: number): Promise<GarmentImage> {
  const { data } = await client.get(`/images/${id}`);
  return data as GarmentImage;
}

export async function fetchFilters(): Promise<FilterFacets> {
  const { data } = await client.get(`/filters`);
  return data.filters as FilterFacets;
}

export async function uploadImage(
  file: File,
  context: UploadContext
): Promise<{ id: number }> {
  const form = new FormData();
  form.append("file", file);
  Object.entries(context).forEach(([k, v]) => {
    if (v) form.append(k, v);
  });
  const { data } = await client.post(`/images/upload`, form);
  return data;
}

export async function deleteImage(id: number): Promise<void> {
  await client.delete(`/images/${id}`);
}

export async function addAnnotation(
  imageId: number,
  payload: { tag?: string; note?: string }
): Promise<Annotation> {
  const { data } = await client.post(`/images/${imageId}/annotations`, payload);
  return data as Annotation;
}

export async function deleteAnnotation(annotationId: number): Promise<void> {
  await client.delete(`/annotations/${annotationId}`);
}
