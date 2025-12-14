from typing import Type
from app.models.source import Source
from .base_scraper import BaseScraper
from .rss_scraper import RSScraper
from .html_scraper import HTMLScraper
from .event_scraper import EventScraper

class ScraperFactory:
    """
    Factory para criar scrapers baseado no tipo da fonte.
    """
    
    _scrapers = {
        'rss': RSScraper,
        'html': HTMLScraper,
        'event': EventScraper,
    }
    
    @classmethod
    def create_scraper(cls, source: Source) -> BaseScraper:
        """
        Cria o scraper apropriado para a fonte.
        
        Args:
            source: Instância da fonte com configurações
            
        Returns:
            Instância do scraper apropriado
            
        Raises:
            ValueError: Se o tipo do scraper não for suportado
        """
        scraper_type = source.scraper_type
        
        if scraper_type not in cls._scrapers:
            raise ValueError(f"Tipo de scraper não suportado: {scraper_type}")
            
        scraper_class = cls._scrapers[scraper_type]
        return scraper_class(source)
    
    @classmethod
    def get_available_types(cls) -> list:
        """Retorna lista dos tipos de scraper disponíveis."""
        return list(cls._scrapers.keys())
    
    @classmethod
    def register_scraper(cls, scraper_type: str, scraper_class: Type[BaseScraper]):
        """Registra um novo tipo de scraper."""
        cls._scrapers[scraper_type] = scraper_class