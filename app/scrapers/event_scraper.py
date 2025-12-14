from typing import List, Dict, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from loguru import logger
from .base_scraper import BaseScraper

class EventScraper(BaseScraper):
    """
    Scraper especializado em eventos geek.
    Focado em sites como Sympla, Eventbrite, e outros agregadores de eventos.
    """
    
    def __init__(self, source):
        super().__init__(source)
        self.event_keywords = [
            'anime', 'manga', 'cosplay', 'comic con', 'games', 'gaming',
            'geek', 'nerd', 'cinema', 'filme', 'série', 'hq', 'quadrinhos',
            'tech', 'tecnologia', 'lan house', 'esports', 'stream'
        ]
        
    async def scrape(self) -> List[Dict[str, Any]]:
        """Extrai eventos de sites especializados"""
        events = []
        
        try:
            config = self.source.scraper_config
            scraper_type = config.get('event_type', 'sympla')
            
            if scraper_type == 'sympla':
                events = await self._scrape_sympla()
            elif scraper_type == 'eventbrite':
                events = await self._scrape_eventbrite()
            elif scraper_type == 'custom':
                events = await self._scrape_custom_events()
                
        except Exception as e:
            logger.error(f"Erro no event scraping: {e}")
            
        return events
        
    async def _scrape_sympla(self) -> List[Dict[str, Any]]:
        """Scraping específico do Sympla"""
        events = []
        
        try:
            # URLs de busca por categoria no Sympla
            search_terms = ['anime', 'games', 'tech', 'cinema', 'geek']
            
            for term in search_terms:
                url = f"https://www.sympla.com.br/eventos?s={term}"
                logger.info(f"Buscando eventos no Sympla: {term}")
                
                html = await self._fetch_url(url)
                if not html:
                    continue
                    
                soup = BeautifulSoup(html, 'html.parser')
                
                # Seletores específicos do Sympla (podem mudar)
                event_cards = soup.select('.EventCard, .event-card, [data-testid="event-card"]')
                
                for card in event_cards[:10]:  # Limita por busca
                    event = self._extract_sympla_event(card)
                    if event and self._is_geek_event(event):
                        events.append(event)
                        
        except Exception as e:
            logger.error(f"Erro no Sympla scraping: {e}")
            
        return events
        
    def _extract_sympla_event(self, card) -> Dict[str, Any]:
        """Extrai dados de um cartão de evento do Sympla"""
        try:
            # Título
            title_elem = card.select_one('.EventCard__title, .event-title, h3, h4')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Link
            link_elem = card.select_one('a')
            link = link_elem.get('href', '') if link_elem else ''
            if link and not link.startswith('http'):
                link = 'https://www.sympla.com.br' + link
                
            # Data
            date_elem = card.select_one('.EventCard__date, .event-date, [data-testid="event-date"]')
            date_str = date_elem.get_text(strip=True) if date_elem else ''
            
            # Local
            location_elem = card.select_one('.EventCard__location, .event-location')
            location = location_elem.get_text(strip=True) if location_elem else ''
            
            # Imagem
            img_elem = card.select_one('img')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            event = {
                'title': title,
                'content': f"Evento: {title}\nLocal: {location}\nData: {date_str}",
                'source_url': link,
                'event_date': self._parse_event_date(date_str),
                'location': location,
                'image_url': image_url,
                'event_type': 'presencial' if location else 'online',
                'source_platform': 'sympla'
            }
            
            return event
            
        except Exception as e:
            logger.error(f"Erro ao extrair evento Sympla: {e}")
            return None
            
    async def _scrape_eventbrite(self) -> List[Dict[str, Any]]:
        """Scraping do Eventbrite (implementação similar)"""
        # Implementação similar ao Sympla
        # Adaptar seletores para o Eventbrite
        return []
        
    async def _scrape_custom_events(self) -> List[Dict[str, Any]]:
        """Scraping de sites customizados de eventos"""
        events = []
        
        try:
            config = self.source.scraper_config
            pages = config.get('event_pages', [])
            
            for page_config in pages:
                url = page_config['url']
                selectors = page_config['selectors']
                
                html = await self._fetch_url(url)
                if not html:
                    continue
                    
                soup = BeautifulSoup(html, 'html.parser')
                
                event_elements = soup.select(selectors.get('event_container', '.event'))
                
                for element in event_elements:
                    event = self._extract_custom_event(element, selectors)
                    if event and self._is_geek_event(event):
                        events.append(event)
                        
        except Exception as e:
            logger.error(f"Erro no custom event scraping: {e}")
            
        return events
        
    def _is_geek_event(self, event: Dict[str, Any]) -> bool:
        """Verifica se o evento é relacionado ao universo geek"""
        text_to_check = f"{event.get('title', '')} {event.get('content', '')}".lower()
        
        return any(keyword in text_to_check for keyword in self.event_keywords)
        
    def _parse_event_date(self, date_str: str) -> datetime:
        """Parse específico para datas de eventos"""
        if not date_str:
            return datetime.now() + timedelta(days=30)  # Default future date
            
        # Remove texto extra comum em datas de eventos
        date_str = date_str.lower()
        date_str = date_str.replace('a partir de', '').replace('a partir do dia', '')
        
        # Tenta diferentes formatos
        formats = [
            '%d/%m/%Y',
            '%d de %B',  # "15 de dezembro"
            '%d %b %Y',
            '%d %B %Y'
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                # Se não tem ano, assume o próximo ano se a data já passou
                if parsed_date.year == 1900:
                    current_year = datetime.now().year
                    parsed_date = parsed_date.replace(year=current_year)
                    if parsed_date < datetime.now():
                        parsed_date = parsed_date.replace(year=current_year + 1)
                        
                return parsed_date
            except ValueError:
                continue
                
        return datetime.now() + timedelta(days=30)