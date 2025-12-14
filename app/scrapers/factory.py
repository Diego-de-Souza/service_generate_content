from typing import Type, Dict, Any, List
from .base_scraper import BaseScraper
from .rss_scraper import RSScraper

class ScraperFactory:
    """
    Factory stateless para criar scrapers sem dependências de banco.
    """
    
    _scrapers = {
        'rss': RSScraper,
    }
    
    @classmethod
    def create_scraper(cls, scraper_type: str, config: Dict[str, Any]) -> 'BaseScraper':
        """
        Cria o scraper apropriado com configuração direta.
        
        Args:
            scraper_type: Tipo do scraper ('rss', 'html', etc)
            config: Configuração do scraper (ex: {'feed_urls': [...]})
            
        Returns:
            Instância do scraper apropriado
            
        Raises:
            ValueError: Se o tipo do scraper não for suportado
        """
        if scraper_type not in cls._scrapers:
            raise ValueError(f"Tipo de scraper não suportado: {scraper_type}")
            
        scraper_class = cls._scrapers[scraper_type]
        return scraper_class(config)
    
    @classmethod
    def get_available_types(cls) -> list:
        """Retorna lista dos tipos de scraper disponíveis."""
        return list(cls._scrapers.keys())
    
    @classmethod
    def register_scraper(cls, scraper_type: str, scraper_class: Type[BaseScraper]):
        """Registra um novo tipo de scraper."""
        cls._scrapers[scraper_type] = scraper_class