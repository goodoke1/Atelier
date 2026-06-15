"""Pydantic models for API responses and requests."""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ImageStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    classified = "classified"
    failed = "failed"


class Annotation(BaseModel):
    id: int
    image_id: int
    tag: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None


class AnnotationCreate(BaseModel):
    tag: Optional[str] = None
    note: Optional[str] = None


class GarmentImage(BaseModel):
    id: int
    filename: str
    original_filename: Optional[str] = None
    uploaded_at: Optional[str] = None
    status: ImageStatus
    error_message: Optional[str] = None

    # AI-generated
    description: Optional[str] = None
    garment_type: Optional[str] = None
    style: Optional[str] = None
    material: Optional[str] = None
    color_palette: Optional[str] = None
    pattern: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None
    consumer_profile: Optional[str] = None
    trend_notes: Optional[str] = None

    # User-supplied context
    location_continent: Optional[str] = None
    location_country: Optional[str] = None
    location_city: Optional[str] = None
    designer: Optional[str] = None
    image_year: Optional[int] = None
    image_month: Optional[int] = None

    annotations: List[Annotation] = []

    @property
    def image_url(self) -> str:
        return f"/api/images/{self.id}/file"
