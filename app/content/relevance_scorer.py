from typing import Dict, List, Any, Optional
import re
from datetime import datetime, timedelta
from collections import Counter
from loguru import logger
import asyncio
import aiohttp

class RelevanceScorer:
    """
    Calcula scores de relevância baseado em múltiplos fatores:
    - Popularidade de keywords
    - Tendências atuais 
    - Engagement histórico
    - Sazonalidade
    - Social signals (quando disponível)
    """
    
    def __init__(self):
        self.trending_keywords = self._load_trending_keywords()
        self.seasonal_keywords = self._load_seasonal_keywords()
        self.category_weights = self._load_category_weights()
        
    def _load_trending_keywords(self) -> Dict[str, float]:
        """
        Carrega keywords em alta no momento.
        Em produção, isso viria de APIs como Google Trends, Twitter, etc.
        """
        # Simulação - em produção conectaria com APIs reais
        return {
            # Games
            'gta 6': 0.95,
            'baldurs gate 3': 0.90,
            'cyberpunk': 0.85,
            'fortnite': 0.80,
            'valorant': 0.75,
            
            # Filmes/Séries
            'marvel': 0.85,
            'netflix': 0.80,
            'disney plus': 0.75,
            'stranger things': 0.70,
            
            # Tech
            'inteligência artificial': 0.95,
            'chatgpt': 0.90,
            'iphone 15': 0.85,
            'tesla': 0.80,
            
            # Anime/Manga
            'one piece': 0.90,
            'demon slayer': 0.85,
            'attack on titan': 0.80,
        }
        
    def _load_seasonal_keywords(self) -> Dict[str, Dict[str, float]]:
        """
        Keywords sazonais por mês.
        """
        return {
            'dezembro': {
                'natal': 0.9,
                'ano novo': 0.85,
                'férias': 0.8,
                'games natal': 0.85
            },
            'janeiro': {
                'lançamentos': 0.8,
                'preview': 0.75,
                'ces': 0.9  # Consumer Electronics Show
            },
            'junho': {
                'e3': 0.95,
                'summer game fest': 0.9,
                'nintendo direct': 0.85
            },
            'outubro': {
                'halloween': 0.85,
                'horror games': 0.9,
                'filmes terror': 0.85
            }
        }
        
    def _load_category_weights(self) -> Dict[str, float]:
        """
        Pesos base por categoria baseado no engajamento histórico.
        """
        return {
            'games': 1.0,      # Categoria mais popular
            'filmes': 0.9,
            'series': 0.85,
            'tecnologia': 0.8,
            'hqs': 0.75,
            'cultura-pop': 0.7
        }
        
    async def calculate_relevance(self, 
                                title: str, 
                                content: str, 
                                category: str,
                                published_date: Optional[datetime] = None) -> float:
        """
        Calcula score de relevância total do conteúdo.
        
        Args:
            title: Título do artigo
            content: Conteúdo do artigo
            category: Categoria do conteúdo
            published_date: Data de publicação (default: agora)
            
        Returns:
            Score de relevância (0-1)
        """
        try:
            if not published_date:
                published_date = datetime.now()
                
            # Combina título e conteúdo para análise
            full_text = f"{title} {content}".lower()
            
            # Calcula componentes do score
            keyword_score = self._calculate_keyword_score(full_text)
            seasonal_score = self._calculate_seasonal_score(full_text, published_date)
            category_score = self._calculate_category_score(category)
            freshness_score = self._calculate_freshness_score(published_date)
            engagement_score = await self._estimate_engagement_score(title, category)
            
            # Combina scores com pesos
            final_score = (
                keyword_score * 0.3 +
                seasonal_score * 0.2 +
                category_score * 0.2 +
                freshness_score * 0.15 +
                engagement_score * 0.15
            )
            
            logger.debug(
                f"Relevance scores - Keyword: {keyword_score:.3f}, "
                f"Seasonal: {seasonal_score:.3f}, Category: {category_score:.3f}, "
                f"Freshness: {freshness_score:.3f}, Engagement: {engagement_score:.3f}, "
                f"Final: {final_score:.3f}"
            )
            
            return min(final_score, 1.0)
            
        except Exception as e:
            logger.error(f"Erro ao calcular relevância: {e}")
            return 0.5  # Score neutro em caso de erro
            
    def _calculate_keyword_score(self, text: str) -> float:
        """
        Calcula score baseado em keywords trending.
        """
        score = 0.0
        matches = 0
        
        for keyword, weight in self.trending_keywords.items():
            if keyword.lower() in text:
                score += weight
                matches += 1
                
        # Normaliza pelo número de matches
        if matches > 0:
            score = score / matches
        else:
            score = 0.3  # Score base para conteúdo sem keywords trending
            
        return min(score, 1.0)
        
    def _calculate_seasonal_score(self, text: str, date: datetime) -> float:
        """
        Calcula score baseado em sazonalidade.
        """
        month_name = date.strftime('%B').lower()
        month_names = {
            'january': 'janeiro',
            'february': 'fevereiro', 
            'march': 'março',
            'april': 'abril',
            'may': 'maio',
            'june': 'junho',
            'july': 'julho',
            'august': 'agosto',
            'september': 'setembro',
            'october': 'outubro',
            'november': 'novembro',
            'december': 'dezembro'
        }
        
        portuguese_month = month_names.get(month_name, month_name)
        
        seasonal_keywords = self.seasonal_keywords.get(portuguese_month, {})
        
        if not seasonal_keywords:
            return 0.5  # Score neutro se não há keywords sazonais
            
        score = 0.0
        matches = 0
        
        for keyword, weight in seasonal_keywords.items():
            if keyword.lower() in text:
                score += weight
                matches += 1
                
        if matches > 0:
            return min(score / matches, 1.0)
        else:
            return 0.4  # Score baixo se não tem keywords sazonais
            
    def _calculate_category_score(self, category: str) -> float:
        """
        Score baseado na popularidade histórica da categoria.
        """
        category_lower = category.lower().replace(' ', '-')
        return self.category_weights.get(category_lower, 0.5)
        
    def _calculate_freshness_score(self, date: datetime) -> float:
        """
        Score baseado na "frescor" do conteúdo.
        Conteúdo mais recente tem score maior.
        """
        now = datetime.now()
        age_hours = (now - date).total_seconds() / 3600
        
        # Score decresce com o tempo
        if age_hours <= 1:
            return 1.0
        elif age_hours <= 6:
            return 0.9
        elif age_hours <= 24:
            return 0.8
        elif age_hours <= 72:
            return 0.7
        elif age_hours <= 168:  # 1 semana
            return 0.5
        else:
            return 0.3
            
    async def _estimate_engagement_score(self, title: str, category: str) -> float:
        """
        Estima score de engagement baseado no título e categoria.
        Em produção, usaria dados reais de engagement.
        """
        # Análise do título
        title_lower = title.lower()
        
        # Palavras que geram engagement
        engaging_words = {
            'exclusivo': 0.9,
            'revelado': 0.8,
            'confirmado': 0.8,
            'oficial': 0.7,
            'trailer': 0.8,
            'gameplay': 0.8,
            'review': 0.7,
            'novidade': 0.6,
            'lançamento': 0.7,
            'breaking': 0.9,
            'primeiro': 0.6,
            'último': 0.6,
            'melhor': 0.5,
            'pior': 0.5,
            'top': 0.6,
            'lista': 0.5
        }
        
        score = 0.4  # Score base
        
        for word, boost in engaging_words.items():
            if word in title_lower:
                score += boost * 0.1  # 10% do boost por palavra
                
        # Boost por tamanho adequado do título
        title_length = len(title)
        if 40 <= title_length <= 70:
            score += 0.1
            
        # Boost por números no título (listas, anos, etc.)
        if re.search(r'\d+', title):
            score += 0.05
            
        return min(score, 1.0)
        
    def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna tópicos em alta no momento.
        
        Args:
            limit: Número máximo de tópicos
            
        Returns:
            Lista de tópicos trending
        """
        # Ordena por peso
        sorted_topics = sorted(
            self.trending_keywords.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        result = []
        for keyword, weight in sorted_topics:
            result.append({
                'keyword': keyword,
                'score': weight,
                'category': self._guess_keyword_category(keyword)
            })
            
        return result
        
    def _guess_keyword_category(self, keyword: str) -> str:
        """
        Tenta adivinhar a categoria de uma keyword.
        """
        keyword_lower = keyword.lower()
        
        if any(word in keyword_lower for word in ['game', 'jogo', 'fps', 'rpg']):
            return 'games'
        elif any(word in keyword_lower for word in ['filme', 'cinema', 'netflix']):
            return 'filmes'
        elif any(word in keyword_lower for word in ['tech', 'iphone', 'ia', 'ai']):
            return 'tecnologia'
        elif any(word in keyword_lower for word in ['anime', 'manga', 'one piece']):
            return 'hqs'
        else:
            return 'cultura-pop'
            
    async def update_trending_keywords(self) -> bool:
        """
        Atualiza keywords trending.
        Em produção, buscaria dados de APIs externas.
        
        Returns:
            True se atualizou com sucesso
        """
        try:
            # Simulação de busca em APIs externas
            # Em produção, integraria com:
            # - Google Trends API
            # - Twitter API
            # - Reddit API
            # - YouTube API
            
            # Por enquanto, apenas simula atualização
            logger.info("Trending keywords atualizadas (simulação)")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar trending keywords: {e}")
            return False
            
    def analyze_competition(self, title: str, content: str) -> Dict[str, Any]:
        """
        Analisa competição do conteúdo no nicho.
        
        Args:
            title: Título do conteúdo
            content: Conteúdo completo
            
        Returns:
            Análise de competição
        """
        # Extrai keywords principais
        keywords = self._extract_main_keywords(f"{title} {content}")
        
        # Calcula competitividade de cada keyword
        competition_scores = {}
        for keyword in keywords[:5]:  # Top 5 keywords
            # Simulação - em produção verificaria volume de busca real
            competition_scores[keyword] = self._estimate_keyword_competition(keyword)
            
        # Calcula score geral de competição
        avg_competition = sum(competition_scores.values()) / len(competition_scores) if competition_scores else 0.5
        
        return {
            'competition_score': avg_competition,
            'keyword_competition': competition_scores,
            'difficulty': self._get_difficulty_level(avg_competition),
            'recommendations': self._get_competition_recommendations(avg_competition)
        }
        
    def _extract_main_keywords(self, text: str) -> List[str]:
        """
        Extrai keywords principais do texto.
        """
        # Remove pontuação e divide em palavras
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stop words
        stop_words = {'de', 'da', 'do', 'a', 'o', 'e', 'para', 'com', 'em', 'na', 'no', 'por'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Conta frequência
        word_counts = Counter(filtered_words)
        
        # Retorna palavras mais frequentes
        return [word for word, count in word_counts.most_common(10) if count > 1]
        
    def _estimate_keyword_competition(self, keyword: str) -> float:
        """
        Estima competição de uma keyword (simulação).
        """
        # Simulação baseada no tamanho da palavra e popularidade
        if keyword in self.trending_keywords:
            return 0.8  # Alta competição para trending
        elif len(keyword) <= 4:
            return 0.9  # Palavras curtas = alta competição
        elif len(keyword) >= 10:
            return 0.3  # Palavras longas = baixa competição
        else:
            return 0.5  # Competição média
            
    def _get_difficulty_level(self, score: float) -> str:
        """
        Converte score numérico em nível de dificuldade.
        """
        if score >= 0.8:
            return 'Muito Alta'
        elif score >= 0.6:
            return 'Alta'
        elif score >= 0.4:
            return 'Média'
        elif score >= 0.2:
            return 'Baixa'
        else:
            return 'Muito Baixa'
            
    def _get_competition_recommendations(self, score: float) -> List[str]:
        """
        Gera recomendações baseadas no nível de competição.
        """
        if score >= 0.8:
            return [
                "Foque em long-tail keywords mais específicas",
                "Adicione ângulos únicos ao conteúdo", 
                "Considere nichos menos competitivos",
                "Invista mais em qualidade e profundidade"
            ]
        elif score >= 0.5:
            return [
                "Boa oportunidade com esforço médio",
                "Adicione valor único ao conteúdo",
                "Otimize bem o SEO"
            ]
        else:
            return [
                "Excelente oportunidade!",
                "Competição baixa, publique rapidamente",
                "Foque em qualidade para dominar o nicho"
            ]