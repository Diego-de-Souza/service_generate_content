from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class UserPreferenceBase(BaseModel):
    preferred_categories: Optional[List[str]] = None
    preferred_personas: Optional[List[str]] = None
    relevance_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    popularity_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    quality_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    content_length_preference: str = Field(default="medium", regex="^(short|medium|long)$")
    update_frequency: str = Field(default="daily", regex="^(hourly|daily|weekly)$")

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreferenceUpdate(BaseModel):
    preferred_categories: Optional[List[str]] = None
    preferred_personas: Optional[List[str]] = None
    relevance_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    popularity_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    quality_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    content_length_preference: Optional[str] = Field(None, regex="^(short|medium|long)$")
    update_frequency: Optional[str] = Field(None, regex="^(hourly|daily|weekly)$")

class UserPreferenceResponse(UserPreferenceBase):
    id: Optional[int] = None
    user_id: str
    interaction_history: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True