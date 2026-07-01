"""Pydantic schemas for the inference API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.config import FEATURE_COLUMNS


class WineFeatures(BaseModel):
    fixed_acidity: float = Field(..., ge=0, description="g/dm³ tartaric acid")
    volatile_acidity: float = Field(..., ge=0, description="g/dm³ acetic acid")
    citric_acid: float = Field(..., ge=0, description="g/dm³")
    residual_sugar: float = Field(..., ge=0, description="g/dm³")
    chlorides: float = Field(..., ge=0, description="g/dm³ sodium chloride")
    free_sulfur_dioxide: float = Field(..., ge=0, description="mg/dm³")
    total_sulfur_dioxide: float = Field(..., ge=0, description="mg/dm³")
    density: float = Field(..., gt=0, description="g/cm³")
    pH: float = Field(..., ge=0, le=14)
    sulphates: float = Field(..., ge=0, description="g/dm³ potassium sulphate")
    alcohol: float = Field(..., ge=0, description="% vol")
    wine_type: int = Field(..., ge=0, le=1, description="0=red, 1=white")

    def to_feature_vector(self) -> list[float]:
        return [getattr(self, col) for col in FEATURE_COLUMNS]


class PredictRequest(BaseModel):
    instances: list[WineFeatures] = Field(..., min_length=1)


class PredictResponse(BaseModel):
    predictions: list[int]
    model_version: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None = None
