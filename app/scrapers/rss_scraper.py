import feedparser
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
from .base_scraper import BaseScraper
from app.core.config import settings

class RSScraper(BaseScraper):
    """
    Scraper especializado em feeds RSS/Atom.
    Ideal para sites de notícias e blogs que disponibilizam feeds.
    """
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Extrai artigos de feeds RSS"""
        articles = []
        
        try:
            # URLs de feeds configuradas diretamente
            feed_urls = self.config.get('feed_urls', [])
            
            # Use aiohttp directly (working method)
            import aiohttp
            
            for feed_url in feed_urls:
                logger.info(f"Processando feed: {feed_url}")
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(feed_url) as response:
                            if response.status == 200:
                                feed_content = await response.text()
                                
                                # Parse do RSS
                                feed = feedparser.parse(feed_content)
                                
                                for entry in feed.entries[:settings.MAX_ARTICLES_PER_REQUEST]:
                                    article = await self._process_rss_entry(entry)
                                    if article:
                                        articles.append(article)
                            else:
                                logger.warning(f"Status {response.status} para {feed_url}")
                                
                except Exception as e:
                    logger.error(f"Erro processando feed {feed_url}: {e}")
                    continue
                        
                # Rate limiting entre feeds
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Erro no RSS scraping: {e}")
            
        return articles
        
    async def _process_rss_entry(self, entry) -> Dict[str, Any]:
        """Processa uma entrada individual do RSS"""
        try:
            # Extrai conteúdo do RSS
            title = entry.get('title', '').strip()
            summary = entry.get('summary', '').strip()
            content = entry.get('content', [{}])
            
            # Prioriza conteúdo completo se disponível
            if content and len(content) > 0:
                full_content = content[0].get('value', summary)
            else:
                full_content = summary
                
            # Se o conteúdo for muito curto, tenta buscar o artigo completo
            if len(full_content) < 300 and entry.get('link'):
                full_content = await self._fetch_full_article(entry.link)
                
            # Extrai metadados
            published = self._parse_date(entry.get('published'))
            
            article = {
                'title': title,
                'content': self._extract_text_content(full_content),
                'summary': self._extract_text_content(summary)[:500],
                'source_url': entry.get('link', ''),
                'published_at': published,
                'author': entry.get('author', ''),
                'categories': [tag.term for tag in entry.get('tags', [])],
                'image_url': self._extract_image_url(entry),
            }
            
            # Calcula score inicial
            article['initial_score'] = self._calculate_content_score(article)
            
            return article
            
        except Exception as e:
            logger.error(f"Erro ao processar entrada RSS: {e}")
            return None
            
    async def _fetch_full_article(self, url: str) -> str:
        """Busca o artigo completo se o RSS só tem resumo"""
        try:
            html = await self._fetch_url(url)
            if html:
                return html
        except Exception as e:
            logger.error(f"Erro ao buscar artigo completo: {e}")
            
        return ""
        
    def _parse_date(self, date_str: str) -> datetime:
        """Converte string de data RSS para datetime"""
        try:
            if date_str:
                # feedparser já parseia a maioria dos formatos
                import time
                return datetime.fromtimestamp(time.mktime(feedparser._parse_date(date_str)))
        except:
            pass
            
        return datetime.now()
        
    def _extract_image_url(self, entry) -> str:
        """Extrai URL da imagem do entry RSS"""
        # Tenta diferentes campos onde pode estar a imagem
        if hasattr(entry, 'media_thumbnail'):
            return entry.media_thumbnail[0]['url']
            
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if 'image' in enclosure.get('type', ''):
                    return enclosure.href
                    
        # Busca no conteúdo HTML
        summary = entry.get('summary', '')
        if '<img' in summary:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(summary, 'html.parser')
            img = soup.find('img')
            if img and img.get('src'):
                return img['src']
                
        return ""