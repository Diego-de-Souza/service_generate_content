from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.source import Source
from app.models.category import Category
from app.scrapers.factory import ScraperFactory
from app.ai.content_rewriter import ContentRewriter
from app.ai.persona_manager import PersonaManager
from app.ai.seo_optimizer import SEOOptimizer
from app.content.relevance_scorer import RelevanceScorer
from app.core.config import settings

class ContentGenerator:
    """
    Orquestrador principal para geração de conteúdo.
    Coordena scraping, reescrita, otimização e scoring.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.content_rewriter = ContentRewriter()
        self.persona_manager = PersonaManager()
        self.seo_optimizer = SEOOptimizer()
        self.relevance_scorer = RelevanceScorer()
        
    async def generate_content_from_sources(self, 
                                          source_ids: Optional[List[int]] = None,
                                          categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Gera conteúdo a partir das fontes configuradas.
        
        Args:
            source_ids: IDs das fontes específicas (opcional)
            categories: Categorias específicas (opcional)
            
        Returns:
            Lista de artigos gerados
        """
        generated_articles = []
        
        try:
            # Busca fontes ativas
            sources = self._get_active_sources(source_ids, categories)
            
            logger.info(f"Iniciando geração de conteúdo para {len(sources)} fontes")
            
            for source in sources:
                logger.info(f"Processando fonte: {source.name}")
                
                # Faz scraping da fonte
                scraped_data = await self._scrape_source(source)
                
                if not scraped_data:
                    logger.warning(f"Nenhum dado coletado de {source.name}")
                    continue
                    
                # Processa cada item coletado
                for item in scraped_data:
                    try:
                        article = await self._process_scraped_item(item, source)
                        if article:
                            generated_articles.append(article)
                    except Exception as e:
                        logger.error(f"Erro ao processar item: {e}")
                        continue
                        
            logger.info(f"Geração concluída: {len(generated_articles)} artigos criados")
            
        except Exception as e:
            logger.error(f"Erro na geração de conteúdo: {e}")
            
        return generated_articles
        
    def _get_active_sources(self, source_ids: Optional[List[int]], categories: Optional[List[str]]) -> List[Source]:
        """
        Busca fontes ativas baseado nos filtros.
        """
        query = self.db.query(Source).filter(Source.is_active == True)
        
        if source_ids:
            query = query.filter(Source.id.in_(source_ids))
            
        if categories:
            # Filtra fontes que cobrem as categorias especificadas
            query = query.filter(Source.category_focus.op('?&')(categories))
            
        return query.all()
        
    async def _scrape_source(self, source: Source) -> List[Dict[str, Any]]:
        """
        Executa scraping de uma fonte específica.
        """
        try:
            # Cria scraper apropriado
            scraper = ScraperFactory.create_scraper(source)
            
            # Executa scraping
            async with scraper:
                data = await scraper.scrape()
                
            # Atualiza última execução
            source.last_scraped = datetime.now()
            source.scraping_errors = 0
            self.db.commit()
            
            return data
            
        except Exception as e:
            logger.error(f"Erro no scraping de {source.name}: {e}")
            
            # Incrementa contador de erros
            source.scraping_errors += 1
            if source.scraping_errors >= 5:
                source.is_active = False
                logger.warning(f"Fonte {source.name} desativada por excesso de erros")
                
            self.db.commit()
            return []
            
    async def _process_scraped_item(self, item: Dict[str, Any], source: Source) -> Optional[Dict[str, Any]]:
        """
        Processa um item coletado transformando em artigo.
        """
        try:
            # Verifica se já existe artigo com a mesma URL
            existing = self.db.query(Article).filter(
                Article.source_url == item.get('source_url')
            ).first()
            
            if existing:
                logger.debug(f"Artigo já existe: {item.get('source_url')}")
                return None
                
            # Determina categoria e persona
            category = self._determine_category(item, source)
            persona = self.persona_manager.suggest_persona_for_category(category.name)
            
            # Calcula score de relevância inicial
            relevance_score = await self.relevance_scorer.calculate_relevance(
                item.get('title', ''), 
                item.get('content', ''),
                category.name
            )
            
            # Só prossegue se o score for suficiente
            if relevance_score < settings.MIN_CONTENT_SCORE:
                logger.debug(f"Score baixo ({relevance_score:.2f}): {item.get('title', '')[:50]}")
                return None
                
            # Reescreve conteúdo
            rewrite_result = await self.content_rewriter.rewrite_content(
                original_content=item.get('content', ''),
                persona=persona,
                category=category.name,
                target_length='medium'
            )
            
            # Verifica originalidade
            if not rewrite_result.get('is_original', False):
                logger.warning(f"Conteúdo não suficientemente original: {item.get('title', '')[:50]}")
                return None
                
            # Gera título e resumo otimizados
            title_summary = await self.content_rewriter.generate_title_and_summary(
                rewrite_result['rewritten_content'], persona
            )
            
            # Otimiza SEO
            seo_data = self.seo_optimizer.optimize_content(
                title=title_summary['title'],
                content=rewrite_result['rewritten_content'],
                category=category.name
            )
            
            # Calcula score final
            final_score = await self._calculate_final_score(
                relevance_score, rewrite_result, seo_data
            )
            
            # Cria artigo
            article_data = {
                'title': seo_data['title'],
                'original_title': item.get('title'),
                'slug': seo_data['slug'],
                'content': seo_data['optimized_content'],
                'summary': title_summary['summary'],
                'meta_title': seo_data['meta_title'],
                'meta_description': seo_data['meta_description'],
                'keywords': seo_data['keywords'],
                'category_id': category.id,
                'persona': persona,
                'source_id': source.id,
                'source_url': item.get('source_url'),
                'relevance_score': relevance_score,
                'final_score': final_score,
                'is_rewritten': True,
                'similarity_score': rewrite_result['similarity_score'],
                'status': 'published' if final_score >= 0.8 else 'draft',
                'featured': final_score >= 0.9,
                'published_at': datetime.now() if final_score >= 0.8 else None
            }
            
            # Salva no banco
            article = Article(**article_data)
            self.db.add(article)
            self.db.commit()
            self.db.refresh(article)
            
            logger.info(f"Artigo criado: {article.title} (Score: {final_score:.2f})")
            
            return {
                'article_id': article.id,
                'title': article.title,
                'score': final_score,
                'status': article.status,
                'persona': persona,
                'category': category.name
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar item: {e}")
            return None
            
    def _determine_category(self, item: Dict[str, Any], source: Source) -> Category:
        """
        Determina a categoria do conteúdo baseado no item e fonte.
        """
        # Primeiro tenta usar categorias da fonte
        if source.category_focus:
            for cat_name in source.category_focus:
                category = self.db.query(Category).filter(
                    Category.name.ilike(f'%{cat_name}%')
                ).first()
                if category:
                    return category
                    
        # Analisa título e conteúdo para determinar categoria
        text_to_analyze = f"{item.get('title', '')} {item.get('content', '')}".lower()
        
        category_keywords = {
            'games': ['jogo', 'game', 'gaming', 'fps', 'rpg', 'mmo', 'console', 'pc', 'mobile'],
            'filmes': ['filme', 'cinema', 'diretor', 'ator', 'netflix', 'streaming', 'oscar'],
            'series': ['série', 'episódio', 'temporada', 'netflix', 'amazon', 'disney'],
            'hqs': ['quadrinho', 'hq', 'comic', 'marvel', 'dc', 'manga', 'anime'],
            'tecnologia': ['tech', 'tecnologia', 'gadget', 'smartphone', 'ia', 'ai', 'software'],
            'cultura-pop': ['cultura', 'pop', 'geek', 'nerd', 'cosplay', 'convention']
        }
        
        best_match = 'cultura-pop'  # Categoria padrão
        max_matches = 0
        
        for category, keywords in category_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if matches > max_matches:
                max_matches = matches
                best_match = category
                
        # Busca ou cria categoria
        category = self.db.query(Category).filter(
            Category.slug == best_match
        ).first()
        
        if not category:
            category = Category(
                name=best_match.replace('-', ' ').title(),
                slug=best_match,
                description=f"Categoria {best_match}",
                is_active=True
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            
        return category
        
    async def _calculate_final_score(self, 
                                   relevance_score: float,
                                   rewrite_result: Dict[str, Any],
                                   seo_data: Dict[str, Any]) -> float:
        """
        Calcula score final combinando múltiplas métricas.
        """
        # Componentes do score
        relevance_weight = 0.4
        quality_weight = 0.3
        seo_weight = 0.2
        originality_weight = 0.1
        
        # Score de qualidade baseado no word count e estrutura
        word_count = rewrite_result.get('word_count', 0)
        quality_score = min(word_count / 500, 1.0) * 0.7 + 0.3  # Normaliza para 0.3-1.0
        
        # Score de originalidade (inverso da similaridade)
        originality_score = 1.0 - rewrite_result.get('similarity_score', 0.5)
        
        # Score SEO
        seo_score = seo_data.get('seo_score', 0.5)
        
        # Cálculo final
        final_score = (
            relevance_score * relevance_weight +
            quality_score * quality_weight +
            seo_score * seo_weight +
            originality_score * originality_weight
        )
        
        return min(final_score, 1.0)
        
    async def generate_personalized_content(self, 
                                          user_id: str,
                                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        Gera conteúdo personalizado baseado nas preferências do usuário.
        
        Args:
            user_id: ID do usuário
            limit: Número máximo de artigos
            
        Returns:
            Lista de artigos personalizados
        """
        try:
            # Busca preferências do usuário
            from app.models.user_preference import UserPreference
            
            user_prefs = self.db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).first()
            
            # Query base de artigos publicados
            query = self.db.query(Article).filter(
                Article.status == 'published'
            )
            
            # Aplica filtros de preferência
            if user_prefs:
                # Filtra por categorias preferidas
                if user_prefs.preferred_categories:
                    category_ids = [
                        cat.id for cat in self.db.query(Category).filter(
                            Category.name.in_(user_prefs.preferred_categories)
                        ).all()
                    ]
                    query = query.filter(Article.category_id.in_(category_ids))
                    
                # Filtra por personas preferidas
                if user_prefs.preferred_personas:
                    query = query.filter(Article.persona.in_(user_prefs.preferred_personas))
                    
                # Ordena por score personalizado
                # Aqui você poderia implementar ML para personalização mais avançada
                
            # Ordena por score e data
            query = query.order_by(
                Article.final_score.desc(),
                Article.published_at.desc()
            ).limit(limit)
            
            articles = query.all()
            
            # Converte para dict
            result = []
            for article in articles:
                result.append({
                    'id': article.id,
                    'title': article.title,
                    'summary': article.summary,
                    'slug': article.slug,
                    'category': article.category.name if article.category else None,
                    'persona': article.persona,
                    'score': article.final_score,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'featured': article.featured
                })
                
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo personalizado: {e}")
            return []
            
    async def update_trending_scores(self) -> int:
        """
        Atualiza scores de trending baseado em métricas recentes.
        
        Returns:
            Número de artigos atualizados
        """
        try:
            # Busca artigos publicados nos últimos 7 dias
            from datetime import timedelta
            
            recent_articles = self.db.query(Article).filter(
                Article.status == 'published',
                Article.published_at >= datetime.now() - timedelta(days=7)
            ).all()
            
            updated_count = 0
            
            for article in recent_articles:
                # Recalcula score de relevância
                new_relevance = await self.relevance_scorer.calculate_relevance(
                    article.title, article.content, article.category.name
                )
                
                # Atualiza scores
                article.relevance_score = new_relevance
                article.final_score = await self._calculate_final_score(
                    new_relevance,
                    {'similarity_score': article.similarity_score, 'word_count': len(article.content.split())},
                    {'seo_score': 0.8}  # Score SEO estimado
                )
                
                # Atualiza status de destaque
                article.featured = article.final_score >= 0.9
                
                updated_count += 1
                
            self.db.commit()
            
            logger.info(f"Scores atualizados para {updated_count} artigos")
            return updated_count
            
        except Exception as e:
            logger.error(f"Erro ao atualizar trending scores: {e}")
            return 0