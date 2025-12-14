from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App Configuration
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Modo Stateless - SEM banco de dados, SEM Redis
    # O serviço apenas processa e retorna dados
    STATELESS_MODE: bool = True
    
    # AI Services (OBRIGATÓRIO)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # Scraping Configuration
    USER_AGENTS: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    SCRAPING_DELAY_MIN: int = 1
    SCRAPING_DELAY_MAX: int = 3
    MAX_CONCURRENT_REQUESTS: int = 10  # Mais agressivo para batch
    
    # Content Generation (Modo Batch)
    MIN_CONTENT_SCORE: float = 0.7
    MAX_ARTICLES_PER_REQUEST: int = 20   # Por request da API NestJS
    MAX_NEWS_PER_REQUEST: int = 15       # Notícias por request
    MAX_FEATURED_PER_REQUEST: int = 10   # Destaques por request
    REWRITE_SIMILARITY_THRESHOLD: float = 0.3
    
    # SEO
    DEFAULT_LANGUAGE: str = "pt-BR"
    SITEMAP_ENABLED: bool = True
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 60
    BURST_LIMIT: int = 100
    
    # Integração com API NestJS
    NESTJS_API_TIMEOUT: int = 300  # 5 minutos timeout
    BATCH_PROCESSING_MODE: bool = True
    RETURN_RAW_DATA: bool = True   # Retorna dados prontos para a API salvar
    
    # Personas Editoriais
    PERSONAS = {
        "games": {
            "tone": "casual e entusiasmado",
            "style": "linguagem gamer, referências técnicas",
            "focus": "gameplay, reviews, news"
        },
        "cinema": {
            "tone": "analítico e cinematográfico", 
            "style": "crítico especializado, referências artísticas",
            "focus": "análises, bastidores, tendências"
        },
        "tech": {
            "tone": "informativo e preciso",
            "style": "técnico mas acessível, foco em inovação",
            "focus": "gadgets, tendências, análises técnicas"
        }
    }
    
    # Fontes de Conteúdo Pré-configuradas (conforme categorias do banco)
    DEFAULT_SOURCES = {
        "animes": [
            {
                "name": "Anime News Network",
                "rss_url": "https://www.animenewsnetwork.com/all/rss.xml",
                "category": "animes"
            },
            {
                "name": "Crunchyroll News",
                "rss_url": "https://www.crunchyroll.com/news/rss",
                "category": "animes"
            }
        ],
        "manga": [
            {
                "name": "Manga Updates",
                "rss_url": "https://www.mangaupdates.com/rss.php",
                "category": "manga"
            },
            {
                "name": "VIZ Media",
                "rss_url": "https://www.viz.com/rss/manga-news",
                "category": "manga"
            }
        ],
        "filmes": [
            {
                "name": "The Verge Entertainment",
                "rss_url": "https://www.theverge.com/entertainment/rss/index.xml",
                "category": "filmes"
            },
            {
                "name": "ComingSoon",
                "rss_url": "https://www.comingsoon.net/feed",
                "category": "filmes"
            },
            {
                "name": "Screen Rant",
                "rss_url": "https://screenrant.com/feed/",
                "category": "filmes"
            }
        ],
        "studios": [
            {
                "name": "Studio Ghibli News",
                "rss_url": "https://www.ghibli.jp/rss/news.xml",
                "category": "studios"
            },
            {
                "name": "Disney Studios",
                "rss_url": "https://www.disney.com/news/rss",
                "category": "studios"
            }
        ],
        "games": [
            {
                "name": "GameSpot",
                "rss_url": "https://www.gamespot.com/feeds/news/",
                "category": "games"
            },
            {
                "name": "IGN Games", 
                "rss_url": "https://feeds.ign.com/ign/games-all",
                "category": "games"
            },
            {
                "name": "Polygon",
                "rss_url": "https://www.polygon.com/rss/index.xml",
                "category": "games"
            }
        ],
        "tech": [
            {
                "name": "TechCrunch",
                "rss_url": "https://techcrunch.com/feed/",
                "category": "tech"
            },
            {
                "name": "Ars Technica",
                "rss_url": "https://feeds.arstechnica.com/arstechnica/index",
                "category": "tech"
            }
        ]
    }
    
    class Config:
        env_file = ".env"

settings = Settings()