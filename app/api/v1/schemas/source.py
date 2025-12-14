from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class SourceBase(BaseModel):
    name: str
    domain: str
    base_url: HttpUrl
    scraper_type: str  # rss, html, event
    scraper_config: Dict[str, Any]
    category_focus: Optional[List[str]] = None
    language: str = "pt-BR"
    country: str = "BR"
    requests_per_minute: int = 10
    delay_between_requests: float = 1.0

class SourceCreate(SourceBase):
    pass

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    scraper_config: Optional[Dict[str, Any]] = None
    category_focus: Optional[List[str]] = None
    is_active: Optional[bool] = None
    requests_per_minute: Optional[int] = None
    delay_between_requests: Optional[float] = None

class SourceResponse(SourceBase):
    id: int
    reliability_score: float
    content_quality: float
    update_frequency: float
    is_active: bool
    last_scraped: Optional[datetime] = None
    scraping_errors: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True