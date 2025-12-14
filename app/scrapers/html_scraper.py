from typing import List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime
from loguru import logger
from .base_scraper import BaseScraper

class HTMLScraper(BaseScraper):
    """
    Scraper para sites que não têm RSS, usando seletores CSS/XPath.
    Requer configuração detalhada dos seletores para cada site.
    """
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Extrai artigos usando seletores HTML configurados"""
        articles = []
        
        try:
            config = self.source.scraper_config
            base_url = self.source.base_url
            
            # Lista de páginas para fazer scraping
            pages = config.get('pages', ['/'])
            
            for page in pages:
                url = base_url.rstrip('/') + page
                logger.info(f"Fazendo scraping de: {url}")
                
                html = await self._fetch_url(url)
                if not html:
                    continue
                    
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extrai links de artigos
                article_links = self._extract_article_links(soup, config)
                
                # Processa cada artigo
                for link in article_links[:settings.MAX_ARTICLES_PER_SCRAPE]:
                    article = await self._process_article_page(link, config)
                    if article:
                        articles.append(article)
                        
        except Exception as e:
            logger.error(f"Erro no HTML scraping: {e}")
            
        return articles
        
    def _extract_article_links(self, soup: BeautifulSoup, config: Dict) -> List[str]:
        """Extrai links de artigos da página principal"""
        links = []
        
        try:
            # Seletor para links de artigos
            link_selector = config.get('article_link_selector')
            if not link_selector:
                return links
                
            elements = soup.select(link_selector)
            
            for element in elements:
                href = element.get('href')
                if href:
                    # Converte link relativo para absoluto
                    if href.startswith('/'):
                        href = self.source.base_url.rstrip('/') + href
                    elif not href.startswith('http'):
                        href = self.source.base_url.rstrip('/') + '/' + href
                        
                    links.append(href)
                    
        except Exception as e:
            logger.error(f"Erro ao extrair links: {e}")
            
        return links
        
    async def _process_article_page(self, url: str, config: Dict) -> Dict[str, Any]:
        """Processa página individual de artigo"""
        try:
            html = await self._fetch_url(url)
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extrai dados usando seletores configurados
            title = self._extract_by_selector(soup, config.get('title_selector'))
            content = self._extract_by_selector(soup, config.get('content_selector'))
            summary = self._extract_by_selector(soup, config.get('summary_selector'))
            author = self._extract_by_selector(soup, config.get('author_selector'))
            date_str = self._extract_by_selector(soup, config.get('date_selector'))
            image_url = self._extract_image_by_selector(soup, config.get('image_selector'))
            
            # Limpa e processa conteúdo
            if content:
                content = self._extract_text_content(str(content))
                
            if not title or not content or len(content) < 100:
                return None
                
            # Parse da data
            published_at = self._parse_date_string(date_str)
            
            article = {
                'title': title.strip(),
                'content': content,
                'summary': summary[:500] if summary else content[:500],
                'source_url': url,
                'published_at': published_at,
                'author': author.strip() if author else '',
                'image_url': image_url,
                'categories': []  # Pode ser extraído se houver seletor
            }
            
            # Calcula score inicial
            article['initial_score'] = self._calculate_content_score(article)
            
            return article
            
        except Exception as e:
            logger.error(f"Erro ao processar artigo {url}: {e}")
            return None
            
    def _extract_by_selector(self, soup: BeautifulSoup, selector: str) -> str:
        """Extrai texto usando seletor CSS"""
        if not selector:
            return ""
            
        try:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        except Exception as e:
            logger.error(f"Erro ao usar seletor {selector}: {e}")
            
        return ""
        
    def _extract_image_by_selector(self, soup: BeautifulSoup, selector: str) -> str:
        """Extrai URL de imagem usando seletor"""
        if not selector:
            return ""
            
        try:
            element = soup.select_one(selector)
            if element:
                # Pode ser img src ou background-image
                if element.name == 'img':
                    return element.get('src', '')
                else:
                    # Tenta extrair de style background-image
                    style = element.get('style', '')
                    if 'background-image' in style:
                        import re
                        match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                        if match:
                            return match.group(1)
        except Exception as e:
            logger.error(f"Erro ao extrair imagem: {e}")
            
        return ""
        
    def _parse_date_string(self, date_str: str) -> datetime:
        """Tenta parsear string de data em vários formatos"""
        if not date_str:
            return datetime.now()
            
        # Formatos comuns de data
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%d de %B de %Y',  # Formato português
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
                
        # Se não conseguiu parsear, usa data atual
        return datetime.now()