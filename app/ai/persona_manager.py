from typing import Dict, Any, List
from app.core.config import settings

class PersonaManager:
    """
    Gerencia as diferentes personas editoriais e seus estilos de escrita.
    """
    
    def __init__(self):
        self.personas = settings.PERSONAS
        
    def get_persona_config(self, persona_name: str) -> Dict[str, Any]:
        """
        Retorna a configuração de uma persona específica.
        
        Args:
            persona_name: Nome da persona (games, cinema, tech)
            
        Returns:
            Configuração da persona
        """
        return self.personas.get(persona_name, self.personas.get('games'))
        
    def get_all_personas(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna todas as personas disponíveis.
        """
        return self.personas
        
    def suggest_persona_for_category(self, category: str) -> str:
        """
        Sugere a persona mais apropriada baseada na categoria do conteúdo.
        
        Args:
            category: Categoria do conteúdo
            
        Returns:
            Nome da persona sugerida
        """
        category_lower = category.lower()
        
        # Mapeamento categoria -> persona
        category_mapping = {
            'games': 'games',
            'jogos': 'games',
            'gaming': 'games',
            'esports': 'games',
            
            'filme': 'cinema',
            'filmes': 'cinema',
            'cinema': 'cinema',
            'série': 'cinema', 
            'séries': 'cinema',
            'tv': 'cinema',
            'streaming': 'cinema',
            
            'tecnologia': 'tech',
            'tech': 'tech',
            'gadget': 'tech',
            'gadgets': 'tech',
            'hardware': 'tech',
            'software': 'tech',
            'ia': 'tech',
            'ai': 'tech'
        }
        
        for key, persona in category_mapping.items():
            if key in category_lower:
                return persona
                
        # Default para games se não encontrar correspondência
        return 'games'
        
    def get_writing_guidelines(self, persona_name: str, content_type: str = 'article') -> Dict[str, Any]:
        """
        Retorna diretrizes específicas de escrita para uma persona.
        
        Args:
            persona_name: Nome da persona
            content_type: Tipo de conteúdo (article, news, review, event)
            
        Returns:
            Diretrizes de escrita
        """
        persona_config = self.get_persona_config(persona_name)
        
        base_guidelines = {
            'tone': persona_config.get('tone'),
            'style': persona_config.get('style'),
            'focus_areas': persona_config.get('focus', '').split(', '),
            'vocabulary_level': self._get_vocabulary_level(persona_name),
            'target_audience': self._get_target_audience(persona_name),
            'content_structure': self._get_content_structure(persona_name, content_type)
        }
        
        # Adiciona diretrizes específicas por tipo de conteúdo
        type_specific = self._get_type_specific_guidelines(persona_name, content_type)
        base_guidelines.update(type_specific)
        
        return base_guidelines
        
    def _get_vocabulary_level(self, persona_name: str) -> str:
        """
        Define o nível de vocabulário para cada persona.
        """
        levels = {
            'games': 'casual_technical',  # Gírias gamer + termos técnicos
            'cinema': 'sophisticated',     # Vocabulário cinematográfico
            'tech': 'technical_accessible' # Técnico mas acessível
        }
        return levels.get(persona_name, 'casual')
        
    def _get_target_audience(self, persona_name: str) -> Dict[str, Any]:
        """
        Define o público-alvo para cada persona.
        """
        audiences = {
            'games': {
                'age_range': '16-35',
                'interests': ['jogos', 'tecnologia', 'competições', 'streaming'],
                'expertise_level': 'intermediário a avançado',
                'preferred_content': ['reviews', 'news', 'guides', 'análises']
            },
            'cinema': {
                'age_range': '18-45', 
                'interests': ['filmes', 'séries', 'cultura', 'arte'],
                'expertise_level': 'iniciante a intermediário',
                'preferred_content': ['reviews', 'análises', 'bastidores', 'listas']
            },
            'tech': {
                'age_range': '20-50',
                'interests': ['tecnologia', 'inovação', 'gadgets', 'ciência'],
                'expertise_level': 'intermediário',
                'preferred_content': ['análises', 'comparações', 'tutoriais', 'news']
            }
        }
        return audiences.get(persona_name, audiences['games'])
        
    def _get_content_structure(self, persona_name: str, content_type: str) -> Dict[str, List[str]]:
        """
        Define estrutura recomendada do conteúdo por persona e tipo.
        """
        structures = {
            'games': {
                'article': ['intro_hook', 'contexto', 'análise_detalhada', 'impacto_comunidade', 'conclusão'],
                'review': ['overview', 'gameplay', 'gráficos', 'som', 'pros_contras', 'nota'],
                'news': ['lead', 'detalhes', 'contexto', 'impacto', 'próximos_passos'],
                'event': ['destaque', 'detalhes', 'como_participar', 'expectativas']
            },
            'cinema': {
                'article': ['intro_cinematográfica', 'contexto_cultural', 'análise_artística', 'relevância', 'conclusão'],
                'review': ['sinopse_breve', 'direção', 'atuações', 'aspectos_técnicos', 'veredicto'],
                'news': ['lead_impactante', 'contexto', 'detalhes', 'repercussão', 'what_next'],
                'event': ['spotlight', 'lineup', 'ingressos', 'expectativas']
            },
            'tech': {
                'article': ['problema_oportunidade', 'solução_tecnológica', 'análise_técnica', 'implicações', 'futuro'],
                'review': ['specs', 'performance', 'usabilidade', 'custo_benefício', 'recomendação'],
                'news': ['breaking', 'background', 'análise_técnica', 'market_impact', 'timeline'],
                'event': ['tech_highlight', 'agenda', 'palestrantes', 'como_participar']
            }
        }
        
        return structures.get(persona_name, {}).get(content_type, ['intro', 'desenvolvimento', 'conclusão'])
        
    def _get_type_specific_guidelines(self, persona_name: str, content_type: str) -> Dict[str, Any]:
        """
        Retorna diretrizes específicas por tipo de conteúdo.
        """
        guidelines = {
            'article': {
                'min_words': 400,
                'max_words': 800,
                'include_sources': True,
                'seo_focus': True
            },
            'news': {
                'min_words': 200,
                'max_words': 500,
                'urgency_tone': True,
                'factual_focus': True
            },
            'review': {
                'min_words': 300,
                'max_words': 1000,
                'include_rating': True,
                'pros_cons_required': True
            },
            'event': {
                'min_words': 150,
                'max_words': 400,
                'include_practical_info': True,
                'call_to_action': True
            }
        }
        
        return guidelines.get(content_type, guidelines['article'])
        
    def validate_persona_content(self, content: str, persona_name: str) -> Dict[str, Any]:
        """
        Valida se o conteúdo está adequado à persona.
        
        Args:
            content: Conteúdo a ser validado
            persona_name: Nome da persona
            
        Returns:
            Resultado da validação com score e sugestões
        """
        guidelines = self.get_writing_guidelines(persona_name)
        validation_result = {
            'is_valid': True,
            'score': 0.0,
            'issues': [],
            'suggestions': []
        }
        
        # Validação de tamanho
        word_count = len(content.split())
        min_words = guidelines.get('min_words', 200)
        max_words = guidelines.get('max_words', 800)
        
        if word_count < min_words:
            validation_result['issues'].append(f'Conteúdo muito curto ({word_count} palavras, mínimo {min_words})')
            validation_result['is_valid'] = False
        elif word_count > max_words:
            validation_result['issues'].append(f'Conteúdo muito longo ({word_count} palavras, máximo {max_words})')
            
        # Validação de tom (análise simples baseada em palavras-chave)
        tone_score = self._analyze_tone_compliance(content, persona_name)
        validation_result['score'] += tone_score * 0.4
        
        # Validação de estilo
        style_score = self._analyze_style_compliance(content, persona_name)
        validation_result['score'] += style_score * 0.4
        
        # Validação de estrutura
        structure_score = self._analyze_structure_compliance(content, persona_name)
        validation_result['score'] += structure_score * 0.2
        
        # Score final
        validation_result['score'] = min(validation_result['score'], 1.0)
        
        if validation_result['score'] < 0.7:
            validation_result['is_valid'] = False
            
        return validation_result
        
    def _analyze_tone_compliance(self, content: str, persona_name: str) -> float:
        """
        Analisa se o tom do conteúdo está adequado à persona.
        """
        # Implementação simplificada - pode ser expandida com NLP mais sofisticado
        persona_config = self.get_persona_config(persona_name)
        expected_tone = persona_config.get('tone', '')
        
        # Palavras-chave por tom
        tone_keywords = {
            'casual': ['galera', 'pessoal', 'cara', 'mano', 'tipo'],
            'entusiasmado': ['incrível', 'fantástico', 'épico', 'sensacional', 'demais'],
            'analítico': ['análise', 'considerando', 'avaliando', 'observa-se', 'constata-se'],
            'técnico': ['especificações', 'performance', 'configuração', 'sistema', 'dados']
        }
        
        content_lower = content.lower()
        matches = 0
        total_keywords = 0
        
        for tone_key, keywords in tone_keywords.items():
            if tone_key in expected_tone.lower():
                total_keywords += len(keywords)
                for keyword in keywords:
                    if keyword in content_lower:
                        matches += 1
                        
        return matches / max(total_keywords, 1)
        
    def _analyze_style_compliance(self, content: str, persona_name: str) -> float:
        """
        Analisa se o estilo do conteúdo está adequado à persona.
        """
        # Análise simplificada de estilo
        score = 0.5  # Score base
        
        if persona_name == 'games':
            # Verifica termos gamers
            gaming_terms = ['gameplay', 'fps', 'rpg', 'mmo', 'pvp', 'raid', 'build', 'nerf', 'buff']
            found_terms = sum(1 for term in gaming_terms if term.lower() in content.lower())
            score += (found_terms / len(gaming_terms)) * 0.3
            
        elif persona_name == 'cinema':
            # Verifica termos cinematográficos
            cinema_terms = ['direção', 'roteiro', 'atuação', 'cinematografia', 'trilha', 'edição']
            found_terms = sum(1 for term in cinema_terms if term in content.lower())
            score += (found_terms / len(cinema_terms)) * 0.3
            
        elif persona_name == 'tech':
            # Verifica termos técnicos
            tech_terms = ['tecnologia', 'inovação', 'algoritmo', 'dados', 'sistema', 'plataforma']
            found_terms = sum(1 for term in tech_terms if term in content.lower())
            score += (found_terms / len(tech_terms)) * 0.3
            
        return min(score, 1.0)
        
    def _analyze_structure_compliance(self, content: str, persona_name: str) -> float:
        """
        Analisa se a estrutura do conteúdo está adequada.
        """
        # Análise básica de estrutura (parágrafos, subtítulos)
        paragraphs = content.split('\n\n')
        has_subtitles = any('#' in p or p.isupper() for p in paragraphs)
        
        score = 0.5
        
        # Bonifica boa estrutura
        if len(paragraphs) >= 3:  # Pelo menos intro, desenvolvimento, conclusão
            score += 0.2
            
        if has_subtitles:
            score += 0.2
            
        if 2 <= len(paragraphs) <= 8:  # Estrutura equilibrada
            score += 0.1
            
        return min(score, 1.0)