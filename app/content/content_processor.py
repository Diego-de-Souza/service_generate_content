from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.user_preference import UserPreference
from app.content.relevance_scorer import RelevanceScorer
from app.ai.persona_manager import PersonaManager

class ContentProcessor:
    """
    Processa e filtra conteúdo para diferentes contextos e usuários.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.relevance_scorer = RelevanceScorer()
        self.persona_manager = PersonaManager()
        
    async def get_trending_content(self, 
                                 limit: int = 20,
                                 category: Optional[str] = None,
                                 persona: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna conteúdo em alta baseado em scores de relevância.
        
        Args:
            limit: Número máximo de artigos
            category: Filtro por categoria (opcional)
            persona: Filtro por persona (opcional)
            
        Returns:
            Lista de artigos trending
        """
        try:
            # Query base - artigos publicados
            query = self.db.query(Article).filter(
                Article.status == 'published'
            )
            
            # Aplica filtros
            if category:
                from app.models.category import Category
                cat = self.db.query(Category).filter(
                    Category.slug == category.lower().replace(' ', '-')
                ).first()
                if cat:
                    query = query.filter(Article.category_id == cat.id)
                    
            if persona:
                query = query.filter(Article.persona == persona)
                
            # Ordena por score de relevância e data
            articles = query.order_by(
                Article.final_score.desc(),
                Article.published_at.desc()
            ).limit(limit).all()
            
            # Converte para formato de resposta
            result = []
            for article in articles:
                result.append({
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'summary': article.summary,
                    'content': article.content,
                    'category': article.category.name if article.category else None,
                    'persona': article.persona,
                    'relevance_score': article.relevance_score,
                    'final_score': article.final_score,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'featured': article.featured,
                    'meta_description': article.meta_description,
                    'keywords': article.keywords,
                    'source_url': article.source_url
                })
                
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar conteúdo trending: {e}")
            return []
            
    async def get_featured_content(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna conteúdo em destaque (featured).
        
        Args:
            limit: Número máximo de artigos
            
        Returns:
            Lista de artigos em destaque
        """
        try:
            articles = self.db.query(Article).filter(
                Article.status == 'published',
                Article.featured == True
            ).order_by(
                Article.final_score.desc(),
                Article.published_at.desc()
            ).limit(limit).all()
            
            result = []
            for article in articles:
                result.append({
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'summary': article.summary,
                    'category': article.category.name if article.category else None,
                    'persona': article.persona,
                    'final_score': article.final_score,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'meta_description': article.meta_description,
                    'image_url': None  # Implementar quando adicionar suporte a imagens
                })
                
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar conteúdo em destaque: {e}")
            return []
            
    async def get_personalized_feed(self, 
                                  user_id: str, 
                                  limit: int = 20,
                                  offset: int = 0) -> Dict[str, Any]:
        """
        Retorna feed personalizado para o usuário.
        
        Args:
            user_id: ID do usuário
            limit: Número máximo de artigos
            offset: Offset para paginação
            
        Returns:
            Feed personalizado com metadados
        """
        try:
            # Busca preferências do usuário
            user_prefs = self.db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).first()
            
            if not user_prefs:
                # Se não tem preferências, retorna trending geral
                articles = await self.get_trending_content(limit)
                return {
                    'articles': articles,
                    'total': len(articles),
                    'personalized': False,
                    'recommendations': ['Configure suas preferências para conteúdo personalizado']
                }
                
            # Query personalizada
            query = self.db.query(Article).filter(
                Article.status == 'published'
            )
            
            # Aplica filtros de preferência
            filters_applied = []
            
            if user_prefs.preferred_categories:
                from app.models.category import Category
                category_ids = [
                    cat.id for cat in self.db.query(Category).filter(
                        Category.name.in_(user_prefs.preferred_categories)
                    ).all()
                ]
                if category_ids:
                    query = query.filter(Article.category_id.in_(category_ids))
                    filters_applied.append(f"Categorias: {', '.join(user_prefs.preferred_categories)}")
                    
            if user_prefs.preferred_personas:
                query = query.filter(Article.persona.in_(user_prefs.preferred_personas))
                filters_applied.append(f"Estilos: {', '.join(user_prefs.preferred_personas)}")
                
            # Calcula score personalizado
            articles_data = query.order_by(
                Article.final_score.desc(),
                Article.published_at.desc()
            ).offset(offset).limit(limit).all()
            
            # Aplica pesos personalizados
            scored_articles = []
            for article in articles_data:
                personalized_score = self._calculate_personalized_score(
                    article, user_prefs
                )
                
                scored_articles.append({
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'summary': article.summary,
                    'category': article.category.name if article.category else None,
                    'persona': article.persona,
                    'original_score': article.final_score,
                    'personalized_score': personalized_score,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'featured': article.featured,
                    'meta_description': article.meta_description
                })
                
            # Reordena por score personalizado
            scored_articles.sort(key=lambda x: x['personalized_score'], reverse=True)
            
            return {
                'articles': scored_articles,
                'total': len(scored_articles),
                'personalized': True,
                'filters_applied': filters_applied,
                'recommendations': self._generate_user_recommendations(user_prefs)
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar feed personalizado: {e}")
            return {
                'articles': [],
                'total': 0,
                'personalized': False,
                'error': str(e)
            }
            
    def _calculate_personalized_score(self, 
                                    article: Article, 
                                    user_prefs: UserPreference) -> float:
        """
        Calcula score personalizado baseado nas preferências do usuário.
        """
        base_score = article.final_score
        
        # Aplica pesos personalizados
        relevance_weight = user_prefs.relevance_weight or 0.4
        popularity_weight = user_prefs.popularity_weight or 0.3
        quality_weight = user_prefs.quality_weight or 0.3
        
        # Recalcula score com pesos personalizados
        personalized_score = (
            (article.relevance_score or 0.5) * relevance_weight +
            (article.popularity_score or 0.5) * popularity_weight +
            (article.quality_score or 0.5) * quality_weight
        )
        
        # Bonus por categoria preferida
        if (user_prefs.preferred_categories and 
            article.category and 
            article.category.name in user_prefs.preferred_categories):
            personalized_score *= 1.1
            
        # Bonus por persona preferida
        if (user_prefs.preferred_personas and 
            article.persona in user_prefs.preferred_personas):
            personalized_score *= 1.1
            
        return min(personalized_score, 1.0)
        
    def _generate_user_recommendations(self, user_prefs: UserPreference) -> List[str]:
        """
        Gera recomendações personalizadas para o usuário.
        """
        recommendations = []
        
        # Analisa preferências atuais
        if not user_prefs.preferred_categories:
            recommendations.append("Adicione categorias favoritas para melhorar a personalização")
            
        if not user_prefs.preferred_personas:
            recommendations.append("Escolha estilos editoriais de sua preferência")
            
        # Sugere novas categorias baseadas no histórico
        if user_prefs.interaction_history:
            # Análise do histórico seria implementada aqui
            recommendations.append("Baseado no seu histórico, você pode gostar de conteúdo sobre tecnologia")
            
        if not recommendations:
            recommendations.append("Seu perfil está bem configurado! Continue explorando.")
            
        return recommendations
        
    async def search_content(self, 
                           query: str,
                           category: Optional[str] = None,
                           persona: Optional[str] = None,
                           limit: int = 20) -> List[Dict[str, Any]]:
        """
        Busca conteúdo baseado em query de texto.
        
        Args:
            query: Texto de busca
            category: Filtro por categoria (opcional)
            persona: Filtro por persona (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de artigos encontrados
        """
        try:
            # Query base
            db_query = self.db.query(Article).filter(
                Article.status == 'published'
            )
            
            # Filtro de busca por título e conteúdo
            search_filter = f"%{query.lower()}%"
            db_query = db_query.filter(
                Article.title.ilike(search_filter) |
                Article.content.ilike(search_filter) |
                Article.summary.ilike(search_filter)
            )
            
            # Filtros adicionais
            if category:
                from app.models.category import Category
                cat = self.db.query(Category).filter(
                    Category.name.ilike(f"%{category}%")
                ).first()
                if cat:
                    db_query = db_query.filter(Article.category_id == cat.id)
                    
            if persona:
                db_query = db_query.filter(Article.persona == persona)
                
            # Ordena por relevância (artigos com query no título primeiro)
            articles = db_query.order_by(
                Article.title.ilike(search_filter).desc(),
                Article.final_score.desc()
            ).limit(limit).all()
            
            # Formata resultado
            result = []
            for article in articles:
                # Calcula relevância da busca
                search_relevance = self._calculate_search_relevance(article, query)
                
                result.append({
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'summary': article.summary,
                    'category': article.category.name if article.category else None,
                    'persona': article.persona,
                    'final_score': article.final_score,
                    'search_relevance': search_relevance,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'highlighted_snippet': self._generate_snippet(article.content, query)
                })
                
            # Reordena por relevância de busca
            result.sort(key=lambda x: x['search_relevance'], reverse=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na busca de conteúdo: {e}")
            return []
            
    def _calculate_search_relevance(self, article: Article, query: str) -> float:
        """
        Calcula relevância do artigo para a busca.
        """
        query_lower = query.lower()
        title_lower = article.title.lower()
        content_lower = article.content.lower()
        
        score = 0.0
        
        # Pontuação por matches no título (peso maior)
        if query_lower in title_lower:
            score += 0.5
            
        # Pontuação por matches no conteúdo
        content_matches = content_lower.count(query_lower)
        score += min(content_matches * 0.1, 0.3)  # Máximo 0.3
        
        # Bonus por match exato
        if query_lower == title_lower:
            score += 0.2
            
        # Combina com score original do artigo
        final_score = (score * 0.7) + (article.final_score * 0.3)
        
        return min(final_score, 1.0)
        
    def _generate_snippet(self, content: str, query: str, max_length: int = 200) -> str:
        """
        Gera snippet destacando a query no conteúdo.
        """
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Encontra posição da query no conteúdo
        pos = content_lower.find(query_lower)
        
        if pos == -1:
            # Se não encontrou, retorna início do conteúdo
            return content[:max_length] + ("..." if len(content) > max_length else "")
            
        # Calcula posição de início do snippet
        start = max(0, pos - 50)
        end = min(len(content), start + max_length)
        
        snippet = content[start:end]
        
        # Adiciona elipses se necessário
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
            
        return snippet
        
    async def get_content_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Retorna analytics do conteúdo dos últimos N dias.
        
        Args:
            days: Número de dias para análise
            
        Returns:
            Dados de analytics
        """
        try:
            from datetime import timedelta
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Query base para o período
            articles = self.db.query(Article).filter(
                Article.published_at >= start_date,
                Article.status == 'published'
            ).all()
            
            if not articles:
                return {'message': 'Nenhum artigo no período especificado'}
                
            # Calcula métricas
            total_articles = len(articles)
            avg_score = sum(a.final_score or 0 for a in articles) / total_articles
            featured_count = sum(1 for a in articles if a.featured)
            
            # Análise por categoria
            category_stats = {}
            for article in articles:
                if article.category:
                    cat_name = article.category.name
                    if cat_name not in category_stats:
                        category_stats[cat_name] = {'count': 0, 'avg_score': 0, 'scores': []}
                    category_stats[cat_name]['count'] += 1
                    category_stats[cat_name]['scores'].append(article.final_score or 0)
                    
            # Calcula médias por categoria
            for cat_name, stats in category_stats.items():
                stats['avg_score'] = sum(stats['scores']) / len(stats['scores'])
                del stats['scores']  # Remove lista temporária
                
            # Análise por persona
            persona_stats = {}
            for article in articles:
                if article.persona:
                    if article.persona not in persona_stats:
                        persona_stats[article.persona] = {'count': 0, 'avg_score': 0}
                    persona_stats[article.persona]['count'] += 1
                    
            return {
                'period_days': days,
                'total_articles': total_articles,
                'average_score': round(avg_score, 3),
                'featured_articles': featured_count,
                'featured_percentage': round((featured_count / total_articles) * 100, 1),
                'category_breakdown': category_stats,
                'persona_breakdown': persona_stats,
                'top_articles': [
                    {
                        'title': a.title,
                        'score': a.final_score,
                        'category': a.category.name if a.category else None
                    }
                    for a in sorted(articles, key=lambda x: x.final_score or 0, reverse=True)[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar analytics: {e}")
            return {'error': str(e)}