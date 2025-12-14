"""
Endpoints batch para integração com API NestJS.
Processa conteúdo sem persistir - retorna dados para a API NestJS salvar.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import asyncio
from loguru import logger

from app.content.stateless_processor import StatelessContentProcessor
from app.core.config import settings

router = APIRouter()

# Schemas de request para aceitar POST com body JSON
class ArticlesRequest(BaseModel):
    category: Optional[str] = None      # animes, manga, filmes, studios, games, tech
    persona: Optional[str] = "games"    # persona editorial
    limit: int = 20                     # máximo de artigos (limite 50)
    min_score: float = 0.7              # score mínimo

# Schemas para resposta conforme modelo do banco NestJS
class ProcessedArticle(BaseModel):
    category: str              # animes, manga, filmes, studios, etc
    title: str                  # título do artigo
    description: str            # pequena descrição do artigo
    text: str                   # artigo completo
    summary: str                # resumo do artigo
    keyWords: List[str]         # palavras-chave
    original_url: str           # rota do artigo original
    source: str                 # fonte do artigo

class ProcessedEvent(BaseModel):
    title: str                  # título do evento
    description: str            # descrição do evento
    location: str               # localização do evento
    date_event: datetime        # data de início do evento
    url_event: str              # URL oficial do evento

class ProcessedNews(BaseModel):
    title: str                  # título da notícia
    disclosure_date: datetime   # data de divulgação

class ArticlesBatchResponse(BaseModel):
    total_processed: int
    articles: List[ProcessedArticle]
    processing_time: float
    cache_used: bool = False
    metadata: dict

class EventsBatchResponse(BaseModel):
    total_processed: int
    events: List[ProcessedEvent]
    processing_time: float
    cache_used: bool = False
    metadata: dict

class NewsBatchResponse(BaseModel):
    total_processed: int
    news: List[ProcessedNews]
    processing_time: float
    cache_used: bool = False
    metadata: dict

@router.post("/articles", response_model=ArticlesBatchResponse)
async def get_processed_articles(request: ArticlesRequest):
    """
    Processa e retorna artigos para a API NestJS salvar.
    Aceita parâmetros via POST JSON body.
    """
    start_time = datetime.now()
    
    try:
        # Validar limit
        if request.limit > 50:
            request.limit = 50
            
        logger.info(f"Processando batch de artigos: categoria={request.category}, persona={request.persona}")
        
        processor = StatelessContentProcessor()
        
        # Processa artigos das fontes configuradas
        articles = await processor.process_batch_articles(
            category=request.category,
            persona=request.persona,
            limit=request.limit,
            min_score=request.min_score
        )
        
        # Converte para formato do banco NestJS
        processed_articles = []
        for article in articles:
            processed_articles.append(ProcessedArticle(
                category=article["category"],        # animes, manga, filmes, studios, games, tech
                title=article["title"],              # título do artigo
                description=article["summary"],       # pequena descrição (usando summary)
                text=article["content"],             # artigo completo
                summary=article["summary"],          # resumo do artigo
                keyWords=article["keywords"],        # palavras-chave
                original_url=article["original_url"], # URL original
                source=article["source"]             # fonte do artigo
            ))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ArticlesBatchResponse(
            total_processed=len(processed_articles),
            articles=processed_articles,
            processing_time=processing_time,
            metadata={
                "sources_used": len(settings.DEFAULT_SOURCES.get(request.category or "games", [])),
                "persona_applied": request.persona,
                "filters": f"category={request.category}, score>={request.min_score}",
                "processing_date": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no processamento batch de artigos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@router.post("/news", response_model=NewsBatchResponse)
async def get_processed_news(
    limit: int = Query(15, le=30, description="Máximo de notícias"),
    hours_ago: int = Query(24, description="Notícias das últimas X horas"),
    min_score: float = Query(0.6, description="Score mínimo para notícias")
):
    """
    Processa e retorna notícias recentes para a API NestJS.
    Foco em conteúdo mais atual e breaking news.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Processando batch de notícias: últimas {hours_ago}h")
        
        processor = StatelessContentProcessor()
        
        # Processa notícias recentes
        news = await processor.process_batch_news(
            limit=limit,
            hours_ago=hours_ago,
            min_score=min_score
        )
        
        # Converte para formato do banco NestJS
        processed_news = []
        for item in news:
            processed_news.append(ProcessedNews(
                title=item["title"],                    # título da notícia
                disclosure_date=item["published_at"]    # data de divulgação
            ))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return NewsBatchResponse(
            total_processed=len(processed_news),
            news=processed_news,
            processing_time=processing_time,
            metadata={
                "time_range": f"últimas {hours_ago} horas",
                "news_focused": True,
                "recency_weight": 0.4,
                "processing_date": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no processamento batch de notícias: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@router.post("/featured", response_model=ArticlesBatchResponse)
async def get_processed_featured(
    limit: int = Query(10, le=20, description="Máximo de destaques"),
    min_score: float = Query(0.85, description="Score mínimo para destaques"),
    mix_categories: bool = Query(True, description="Misturar categorias")
):
    """
    Processa e retorna conteúdo em destaque para a API NestJS.
    Apenas conteúdo de alta qualidade e relevância.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Processando batch de destaques: score>={min_score}")
        
        processor = StatelessContentProcessor()
        
        # Processa conteúdo destacado
        featured = await processor.process_batch_featured(
            limit=limit,
            min_score=min_score,
            mix_categories=mix_categories
        )
        
        # Converte para formato da API
        processed_featured = []
        for item in featured:
            processed_featured.append(ProcessedArticle(
                category=item["category"],
                title=item["title"],
                description=item["summary"],
                text=item["content"],
                summary=item["summary"],
                keyWords=item["keywords"],
                original_url=item["original_url"],
                source=item["source"]
            ))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ArticlesBatchResponse(
            total_processed=len(processed_featured),
            articles=processed_featured,
            processing_time=processing_time,
            metadata={
                "quality_threshold": min_score,
                "featured_content": True,
                "mixed_categories": mix_categories,
                "processing_date": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no processamento batch de eventos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@router.post("/events", response_model=EventsBatchResponse)
async def get_processed_events(
    limit: int = Query(10, le=30, description="Máximo de eventos"),
    days_ahead: int = Query(30, description="Eventos dos próximos X dias"),
    location_filter: Optional[str] = Query(None, description="Filtrar por localização")
):
    """
    Processa e retorna eventos para a API NestJS.
    Foco em eventos geek, conventions, lançamentos, etc.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Processando batch de eventos: próximos {days_ahead} dias")
        
        processor = StatelessContentProcessor()
        
        # Processa eventos
        events = await processor.process_batch_events(
            limit=limit,
            days_ahead=days_ahead,
            location_filter=location_filter
        )
        
        # Converte para formato do banco NestJS
        processed_events = []
        for event in events:
            processed_events.append(ProcessedEvent(
                title=event["title"],                    # título do evento
                description=event["description"],        # descrição do evento
                location=event["location"],              # localização
                date_event=event["date_event"],          # data de início
                url_event=event["url_event"]             # URL oficial
            ))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return EventsBatchResponse(
            total_processed=len(processed_events),
            events=processed_events,
            processing_time=processing_time,
            metadata={
                "time_range": f"próximos {days_ahead} dias",
                "location_filter": location_filter,
                "events_focused": True,
                "processing_date": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no processamento batch de destaques: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@router.get("/health")
async def batch_health_check():
    """
    Health check específico para o modo batch.
    Verifica se o serviço está pronto para processar.
    """
    try:
        # Testa APIs de IA
        from app.ai.content_rewriter import ContentRewriter
        rewriter = ContentRewriter()
        
        # Testa fontes configuradas
        sources_count = sum(len(sources) for sources in settings.DEFAULT_SOURCES.values())
        
        # Teste de conectividade simples
        # Sem Redis - serviço totalmente stateless
        
        return {
            "status": "healthy",
            "mode": "stateless_batch",
            "ai_services": {
                "gemini_configured": bool(settings.GOOGLE_API_KEY)
            },
            "sources_configured": sources_count,
            "cache_available": False,
            "ready_for_batch": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/sources")
async def list_configured_sources():
    """
    Lista fontes configuradas para cada categoria.
    Útil para debug e monitoramento.
    """
    return {
        "sources": settings.DEFAULT_SOURCES,
        "total_sources": sum(len(sources) for sources in settings.DEFAULT_SOURCES.values()),
        "categories": list(settings.DEFAULT_SOURCES.keys())
    }

@router.get("/debug/scrape/{category}")
async def debug_scrape_category(category: str):
    """
    Endpoint de debug para testar scraping de uma categoria específica.
    """
    try:
        processor = StatelessContentProcessor()
        sources = processor._get_sources_for_category(category)
        
        results = []
        for source in sources:
            try:
                # Test direct RSS fetch
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(source["rss_url"]) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Parse with feedparser
                            import feedparser
                            feed = feedparser.parse(content)
                            
                            results.append({
                                "source_name": source["name"],
                                "rss_url": source["rss_url"],
                                "status": response.status,
                                "items_found": len(feed.entries),
                                "sample_titles": [entry.get("title", "N/A") for entry in feed.entries[:3]]
                            })
                        else:
                            results.append({
                                "source_name": source["name"],
                                "rss_url": source["rss_url"],
                                "status": response.status,
                                "error": f"HTTP {response.status}"
                            })
                
            except Exception as e:
                results.append({
                    "source_name": source["name"],
                    "rss_url": source["rss_url"],
                    "error": str(e)
                })
        
        return {
            "category": category,
            "sources_tested": len(sources),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Erro no debug de scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")