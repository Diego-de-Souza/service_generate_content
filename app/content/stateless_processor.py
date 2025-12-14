"""
ContentProcessor otimizado para modo stateless/batch.
Processa conteúdo das fontes e retorna dados para API NestJS salvar.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import asyncio
import json
import hashlib

from app.scrapers.scraper_factory import ScraperFactory
from app.ai.content_rewriter import ContentRewriter
from app.content.relevance_scorer import RelevanceScorer
from app.ai.persona_manager import PersonaManager
from app.core.config import settings

class StatelessContentProcessor:
    """
    Processador de conteúdo sem persistência em banco.
    Ideal para modo batch com API NestJS.
    """
    
    def __init__(self):
        self.scraper_factory = ScraperFactory()
        self.content_rewriter = ContentRewriter()
        self.relevance_scorer = RelevanceScorer()
        self.persona_manager = PersonaManager()
        
        # Modo completamente stateless - sem cache
        logger.info("Iniciando em modo stateless - sem cache")
    
    async def process_batch_articles(self, 
                                   category: Optional[str] = None,
                                   persona: str = "games",
                                   limit: int = 20,
                                   min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Processa batch de artigos para a API NestJS.
        """
        logger.info(f"Processando batch de artigos: {category}/{persona}")
        
        # Determina fontes baseado na categoria
        sources = self._get_sources_for_category(category)
        
        # Modo stateless - sem cache, sempre processa fresh
        
        # Processa conteúdo das fontes
        all_articles = []
        
        for source in sources:
            try:
                scraper = self.scraper_factory.create_scraper(
                    scraper_type="rss",
                    config={"feed_urls": [source["rss_url"]]}
                )
                
                # Scrape da fonte
                scraped_content = await scraper.scrape()
                
                # Processa cada item
                for item in scraped_content[:10]:  # Limita por fonte
                    processed = await self._process_single_article(
                        item, source, persona, category
                    )
                    
                    if processed and processed["final_score"] >= min_score:
                        all_articles.append(processed)
                        
            except Exception as e:
                logger.error(f"Erro processando fonte {source['name']}: {e}")
                continue
        
        # Ordena por score e limita
        all_articles.sort(key=lambda x: x["final_score"], reverse=True)
        final_articles = all_articles[:limit]
        
        # Modo stateless - sem cache, retorna resultados diretamente
        
        return final_articles
    
    async def process_batch_news(self, 
                               limit: int = 15,
                               hours_ago: int = 24,
                               min_score: float = 0.6) -> List[Dict[str, Any]]:
        """
        Processa notícias recentes (últimas X horas).
        """
        logger.info(f"Processando notícias das últimas {hours_ago}h")
        
        # Todas as fontes para news
        all_sources = []
        for category_sources in settings.DEFAULT_SOURCES.values():
            all_sources.extend(category_sources)
        
        recent_articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours_ago)
        
        for source in all_sources:
            try:
                scraper = self.scraper_factory.create_scraper(
                    scraper_type="rss",
                    config={"feed_urls": [source["rss_url"]]}
                )
                
                scraped_content = await scraper.scrape()
                
                for item in scraped_content[:5]:  # Menos por fonte para news
                    # Verifica se é recente
                    pub_date = item.get("published_at", datetime.now())
                    if isinstance(pub_date, str):
                        try:
                            pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        except Exception:
                            pub_date = datetime.now()
                    
                    if pub_date < cutoff_time:
                        continue
                    
                    processed = await self._process_single_article(
                        item, source, "games", source["category"]
                    )
                    
                    if processed and processed["final_score"] >= min_score:
                        # Boost para recência
                        age_hours = (datetime.now() - pub_date).total_seconds() / 3600
                        recency_boost = max(0.1, 0.4 - (age_hours / hours_ago) * 0.3)
                        processed["final_score"] += recency_boost
                        
                        recent_articles.append(processed)
                        
            except Exception as e:
                logger.error(f"Erro processando notícias de {source['name']}: {e}")
                continue
        
        # Ordena por recência e score
        recent_articles.sort(
            key=lambda x: (x["published_at"], x["final_score"]), 
            reverse=True
        )
        
        return recent_articles[:limit]
    
    async def process_batch_featured(self, 
                                   limit: int = 10,
                                   min_score: float = 0.85,
                                   mix_categories: bool = True) -> List[Dict[str, Any]]:
        """Processa conteúdo de destaque (alta qualidade)."""
        logger.info(f"Processando destaques com score >= {min_score}")
        
        featured_articles = []
        
        if mix_categories:
            # Processa todas as categorias
            for category in settings.DEFAULT_SOURCES.keys():
                category_articles = await self.process_batch_articles(
                    category=category,
                    limit=limit // len(settings.DEFAULT_SOURCES),
                    min_score=min_score
                )
                featured_articles.extend(category_articles)
        else:
            # Apenas games (categoria principal)
            featured_articles = await self.process_batch_articles(
                category="games",
                limit=limit,
                min_score=min_score
            )
        
        # Filtra apenas os melhores e marca como featured
        top_articles = []
        for article in featured_articles:
            if article["final_score"] >= min_score:
                article["featured"] = True
                top_articles.append(article)
        
        # Ordena e limita
        top_articles.sort(key=lambda x: x["final_score"], reverse=True)
        return top_articles[:limit]
    
    async def process_batch_events(self,
                                 limit: int = 10,
                                 days_ahead: int = 30,
                                 location_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Processa eventos geek (conventions, lançamentos, etc.)."""
        logger.info(f"Processando eventos dos próximos {days_ahead} dias")
        
        events = []
        future_date = datetime.now() + timedelta(days=days_ahead)
        
        # Fontes de eventos (você pode expandir isso)
        event_sources = [
            {
                "name": "Eventbrite Geek",
                "rss_url": "https://www.eventbrite.com/rss/organizer_list_events/123456789",
                "type": "events"
            },
            {
                "name": "Comic Con Events",
                "rss_url": "https://www.comic-con.org/events.rss",
                "type": "events"
            }
        ]
        
        for source in event_sources:
            try:
                scraper = self.scraper_factory.create_scraper(
                    scraper_type="rss",
                    config={"feed_urls": [source["rss_url"]]}
                )
                
                scraped_content = await scraper.scrape()
                
                for item in scraped_content[:5]:  # Limita por fonte
                    event_data = await self._process_single_event(item, source)
                    
                    if event_data:
                        # Filtra por data futura
                        event_date = event_data["date_event"]
                        if event_date <= future_date:
                            # Filtra por localização se especificado
                            if not location_filter or location_filter.lower() in event_data["location"].lower():
                                events.append(event_data)
                                
            except Exception as e:
                logger.error(f"Erro processando eventos de {source['name']}: {e}")
                continue
        
        # Ordena por data do evento
        events.sort(key=lambda x: x["date_event"])
        return events[:limit]
    
    async def _process_single_article(self, 
                                     item: Dict[str, Any],
                                     source: Dict[str, str],
                                     persona: str,
                                     category: str) -> Optional[Dict[str, Any]]:
        """Processa um único artigo."""
        try:
            # Reescreve conteúdo com IA
            rewritten = await self.content_rewriter.rewrite_content(
                title=item.get("title", ""),
                content=item.get("content", item.get("summary", "")),
                persona=persona
            )
            
            # Calcula scores
            relevance_score = self.relevance_scorer.calculate_relevance(
                title=rewritten["title"],
                content=rewritten["content"],
                category=category
            )
            
            quality_score = await self._calculate_quality_score(rewritten)
            final_score = (relevance_score * 0.6) + (quality_score * 0.4)
            
            # Gera slug
            slug = self._generate_slug(rewritten["title"])
            
            return {
                "title": rewritten["title"],
                "slug": slug,
                "content": rewritten["content"],
                "summary": rewritten["summary"],
                "category": category,
                "persona": persona,
                "keywords": rewritten["keywords"],
                "meta_description": rewritten["meta_description"],
                "original_url": item.get("url", ""),
                "source": source["name"],
                "relevance_score": round(relevance_score, 3),
                "quality_score": round(quality_score, 3),
                "final_score": round(final_score, 3),
                "published_at": item.get("published_at", datetime.now()),
                "featured": final_score >= 0.9
            }
            
        except Exception as e:
            logger.error(f"Erro processando artigo {item.get('title', 'N/A')}: {e}")
            return None
    
    def _get_sources_for_category(self, category: Optional[str]) -> List[Dict[str, str]]:
        """Retorna fontes para uma categoria específica."""
        if category and category in settings.DEFAULT_SOURCES:
            return settings.DEFAULT_SOURCES[category]
        
        # Se não especificado, retorna games (padrão)
        return settings.DEFAULT_SOURCES.get("games", [])
    
    async def _calculate_quality_score(self, content: Dict[str, str]) -> float:
        """Calcula score de qualidade do conteúdo."""
        score = 0.0
        
        # Tamanho do conteúdo
        content_length = len(content.get("content", ""))
        if content_length > 500:
            score += 0.3
        elif content_length > 200:
            score += 0.2
        
        # Qualidade do título
        title = content.get("title", "")
        if len(title) > 20 and len(title) < 100:
            score += 0.2
        
        # Presença de keywords
        if content.get("keywords") and len(content["keywords"]) >= 3:
            score += 0.2
        
        # Meta description
        if content.get("meta_description") and len(content["meta_description"]) > 50:
            score += 0.2
        
        # Summary quality
        summary = content.get("summary", "")
        if len(summary) > 100:
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_slug(self, title: str) -> str:
        """Gera slug a partir do título."""
        import re
        import unicodedata
        
        # Remove acentos
        slug = unicodedata.normalize('NFD', title.lower())
        slug = slug.encode('ascii', 'ignore').decode('ascii')
        
        # Substitui espaços e caracteres especiais
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug.strip())
        
        # Remove hífens duplos
        slug = re.sub(r'-+', '-', slug)
        
        return slug[:100]  # Limita tamanho
    
    async def _process_single_event(self,
                                   item: Dict[str, Any],
                                   source: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Processa um único evento."""
        try:
            # Extrai dados do evento
            title = item.get("title", "")
            description = item.get("description", item.get("summary", ""))
            
            # Tenta extrair localização do conteúdo
            location = self._extract_location(description)
            
            # Tenta extrair data do evento
            event_date = self._extract_event_date(item, description)
            
            # URL do evento
            url_event = item.get("link", item.get("url", ""))
            
            return {
                "title": title,
                "description": description[:500],  # Limita descrição
                "location": location,
                "date_event": event_date,
                "url_event": url_event
            }
            
        except Exception as e:
            logger.error(f"Erro processando evento {item.get('title', 'N/A')}: {e}")
            return None
    
    def _extract_location(self, text: str) -> str:
        """Extrai localização do texto do evento."""
        import re
        
        # Padrões comuns de localização
        patterns = [
            r"(?i)(em|in|at|local:?)\s+([^,\n]{3,50})",
            r"(?i)(local|location|venue):?\s*([^,\n]{3,50})",
            r"(?i)([A-Z][a-z]+,?\s+[A-Z]{2,})",  # Cidade, Estado
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(2).strip() if len(match.groups()) > 1 else match.group(1).strip()
        
        return "Online/Virtual"  # Padrão se não encontrar
    
    def _extract_event_date(self, item: Dict[str, Any], description: str) -> datetime:
        """Extrai data do evento."""
        import re
        from dateutil.parser import parse
        
        # Primeiro tenta a data de publicação
        pub_date = item.get("published_at")
        if pub_date and isinstance(pub_date, str):
            try:
                return datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            except Exception:
                pass
        elif isinstance(pub_date, datetime):
            return pub_date
        
        # Tenta extrair data do título ou descrição
        date_patterns = [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
            r"(\d{4}-\d{2}-\d{2})",
            r"(?i)(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+\d{1,2},?\s+\d{4}"
        ]
        
        full_text = f"{item.get('title', '')} {description}"
        
        for pattern in date_patterns:
            match = re.search(pattern, full_text)
            if match:
                try:
                    return parse(match.group(1))
                except Exception:
                    continue
        
        # Se não encontrar, assume próximos 30 dias
        return datetime.now() + timedelta(days=15)

# Alias para compatibilidade
ContentProcessor = StatelessContentProcessor