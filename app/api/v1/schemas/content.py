from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ArticleResponse(BaseModel):
    id: int
    title: str
    slug: str
    summary: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    persona: Optional[str] = None
    relevance_score: Optional[float] = None
    final_score: Optional[float] = None
    published_at: Optional[str] = None
    featured: bool = False
    meta_description: Optional[str] = None
    keywords: Optional[List[str]] = None
    source_url: Optional[str] = None

class SearchResponse(BaseModel):
    id: int
    title: str
    slug: str
    summary: Optional[str] = None
    category: Optional[str] = None
    persona: Optional[str] = None
    final_score: Optional[float] = None
    search_relevance: float
    published_at: Optional[str] = None
    highlighted_snippet: Optional[str] = None

class TrendingResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    trending_topics: Optional[List[Dict[str, Any]]] = None

class PersonalizedFeedResponse(BaseModel):
    articles: List[Dict[str, Any]]
    total: int
    personalized: bool
    filters_applied: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    error: Optional[str] = None

class GenerateContentRequest(BaseModel):
    source_ids: Optional[List[int]] = None
    categories: Optional[List[str]] = None

class ContentAnalyticsResponse(BaseModel):
    period_days: int
    total_articles: int
    average_score: float
    featured_articles: int
    featured_percentage: float
    category_breakdown: Dict[str, Any]
    persona_breakdown: Dict[str, Any]
    top_articles: List[Dict[str, Any]]