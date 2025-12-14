from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
import time
import random
from loguru import logger
from app.core.config import settings

class BaseScraper(ABC):
    """
    Classe base para todos os scrapers - versão stateless.
    Implementa funcionalidades comuns como rate limiting, headers, etc.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        self.user_agents = [settings.USER_AGENTS] if isinstance(settings.USER_AGENTS, str) else settings.USER_AGENTS
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self._get_headers()
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def _get_headers(self) -> Dict[str, str]:
        """Gera headers realistas para evitar bloqueios"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    async def _rate_limit(self):
        """Implementa rate limiting baseado nas configurações do app"""
        delay = random.uniform(
            settings.SCRAPING_DELAY_MIN,
            settings.SCRAPING_DELAY_MAX
        )
        await asyncio.sleep(delay)
        
    async def _fetch_url(self, url: str) -> Optional[str]:
        """Faz requisição HTTP com tratamento de erros"""
        try:
            await self._rate_limit()
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Status {response.status} para {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erro ao acessar {url}: {e}")
            return None
            
    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """Método principal de scraping - deve ser implementado por cada scraper"""
        pass
        
    def _extract_text_content(self, html: str) -> str:
        """Extração limpa de texto do HTML"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts e estilos
        for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
            element.decompose()
            
        # Extrai texto limpo
        text = soup.get_text(separator=' ', strip=True)
        
        # Limpa espaços extras
        text = ' '.join(text.split())
        
        return text
        
    def _calculate_content_score(self, content: Dict[str, Any]) -> float:
        """Calcula score inicial do conteúdo baseado em métricas simples"""
        score = 0.5  # Score base
        
        # Pontuação por tamanho do conteúdo
        content_length = len(content.get('content', ''))
        if content_length > 1000:
            score += 0.2
        elif content_length > 500:
            score += 0.1
            
        # Pontuação por título atrativo
        title = content.get('title', '')
        if len(title) > 10 and len(title) < 100:
            score += 0.1
            
        # Pontuação por imagens
        if content.get('image_url'):
            score += 0.1
            
        return min(score, 1.0)