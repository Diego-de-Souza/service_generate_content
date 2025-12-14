from typing import Dict, Any, Optional
import openai
from anthropic import Anthropic
from loguru import logger
from app.core.config import settings
from .similarity_checker import SimilarityChecker

class ContentRewriter:
    """
    Responsável pela reescrita inteligente de conteúdo.
    Garante originalidade e qualidade editorial.
    """
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # Inicializa clientes de IA se as chaves estiverem disponíveis
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai
            
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            
        self.similarity_checker = SimilarityChecker()
        
    async def rewrite_content(self, 
                            original_content: str,
                            persona: str,
                            category: str,
                            target_length: str = "medium") -> Dict[str, Any]:
        """
        Reescreve o conteúdo mantendo a informação mas criando texto original.
        
        Args:
            original_content: Conteúdo original a ser reescrito
            persona: Persona editorial (games, cinema, tech)
            category: Categoria do conteúdo
            target_length: Tamanho desejado (short, medium, long)
            
        Returns:
            Dict com conteúdo reescrito e métricas
        """
        try:
            # Prepara o prompt baseado na persona
            prompt = self._build_rewrite_prompt(
                original_content, persona, category, target_length
            )
            
            # Tenta diferentes modelos de IA
            rewritten_content = None
            
            if self.anthropic_client:
                rewritten_content = await self._rewrite_with_anthropic(prompt)
            elif self.openai_client:
                rewritten_content = await self._rewrite_with_openai(prompt)
            else:
                raise ValueError("Nenhum serviço de IA configurado")
                
            if not rewritten_content:
                raise ValueError("Falha na reescrita do conteúdo")
                
            # Verifica similaridade para garantir originalidade
            similarity_score = await self.similarity_checker.calculate_similarity(
                original_content, rewritten_content
            )
            
            # Se muito similar, tenta reescrever novamente com prompt mais agressivo
            if similarity_score > settings.REWRITE_SIMILARITY_THRESHOLD:
                logger.warning(f"Similaridade muito alta ({similarity_score}), reescrevendo...")
                aggressive_prompt = self._build_aggressive_rewrite_prompt(
                    original_content, persona, category
                )
                
                if self.anthropic_client:
                    rewritten_content = await self._rewrite_with_anthropic(aggressive_prompt)
                else:
                    rewritten_content = await self._rewrite_with_openai(aggressive_prompt)
                    
                # Recalcula similaridade
                similarity_score = await self.similarity_checker.calculate_similarity(
                    original_content, rewritten_content
                )
                
            return {
                'rewritten_content': rewritten_content,
                'similarity_score': similarity_score,
                'persona_used': persona,
                'word_count': len(rewritten_content.split()),
                'is_original': similarity_score < settings.REWRITE_SIMILARITY_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Erro na reescrita de conteúdo: {e}")
            raise
            
    def _build_rewrite_prompt(self, content: str, persona: str, category: str, length: str) -> str:
        """
        Constrói prompt para reescrita baseado na persona e categoria.
        """
        persona_config = settings.PERSONAS.get(persona, {})
        tone = persona_config.get('tone', 'informativo')
        style = persona_config.get('style', 'jornalístico')
        
        length_instructions = {
            'short': 'em até 200 palavras',
            'medium': 'entre 300-600 palavras', 
            'long': 'entre 800-1200 palavras'
        }
        
        prompt = f"""
Você é um redator especializado em conteúdo geek e cultura pop. Sua tarefa é reescrever completamente o texto a seguir, mantendo as informações factuais mas criando um texto 100% original.

PERSONA EDITORIAL: {persona.upper()}
- Tom: {tone}
- Estilo: {style}
- Categoria: {category}

REQUISITOS OBRIGATÓRIOS:
✅ NUNCA copie frases ou parágrafos inteiros
✅ Reescreva COMPLETAMENTE com suas próprias palavras
✅ Mantenha todos os fatos e informações importantes
✅ Use linguagem {tone} e {style}
✅ Escreva {length_instructions.get(length, 'entre 300-600 palavras')}
✅ Adicione insights editoriais quando apropriado
✅ Use subtítulos para organizar o conteúdo
✅ Seja envolvente e atrativo para o público geek

TEXTO ORIGINAL PARA REESCREVER:
{content}

TEXTO REESCRITO (100% ORIGINAL):"""
        
        return prompt
        
    def _build_aggressive_rewrite_prompt(self, content: str, persona: str, category: str) -> str:
        """
        Prompt mais agressivo para garantir originalidade quando a primeira tentativa foi muito similar.
        """
        return f"""
ATENÇÃO: A primeira versão ficou muito similar ao original. Você DEVE reescrever de forma MAIS CRIATIVA e ORIGINAL.

Tarefa: Criar um artigo COMPLETAMENTE NOVO baseado apenas nos FATOS do texto original.

PERSONA: {persona.upper()}
CATEGORIA: {category}

ESTRATÉGIAS OBRIGATÓRIAS:
🔥 Mude a estrutura narrativa completamente
🔥 Use vocabulário e expressões diferentes
🔥 Adicione contexto e análise própria
🔥 Reorganize as informações em nova ordem
🔥 Inclua comparações e referências da cultura geek
🔥 Crie novos ângulos de abordagem

TEXTO ORIGINAL (APENAS PARA EXTRAIR FATOS):
{content}

ARTIGO COMPLETAMENTE REESCRITO E ORIGINAL:"""
        
    async def _rewrite_with_anthropic(self, prompt: str) -> str:
        """
        Reescreve usando Claude da Anthropic.
        """
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.8,  # Maior criatividade
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Erro com Anthropic API: {e}")
            return None
            
    async def _rewrite_with_openai(self, prompt: str) -> str:
        """
        Reescreve usando GPT da OpenAI.
        """
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um redator especialista em reescrita de conteúdo geek, focado em criar textos 100% originais mantendo informações factuais."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Erro com OpenAI API: {e}")
            return None
            
    async def generate_title_and_summary(self, content: str, persona: str) -> Dict[str, str]:
        """
        Gera título atrativo e resumo baseado no conteúdo reescrito.
        """
        prompt = f"""
Baseado no artigo abaixo, crie:

1. Um TÍTULO atrativo e otimizado para SEO (máximo 60 caracteres)
2. Um RESUMO envolvente (máximo 160 caracteres)

Persona: {persona.upper()}
Requisitos:
- Título deve ser clickbait mas honesto
- Resumo deve despertar curiosidade
- Use palavras-chave relevantes
- Linguagem apropriada para o público geek

ARTIGO:
{content}

RESPOSTA:
TÍTULO: [seu título aqui]
RESUMO: [seu resumo aqui]"""
        
        try:
            if self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=200,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text.strip()
            elif self.openai_client:
                response = await self.openai_client.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.7
                )
                result = response.choices[0].message.content.strip()
            else:
                return {'title': 'Título não gerado', 'summary': 'Resumo não gerado'}
                
            # Parse da resposta
            lines = result.split('\n')
            title = ''
            summary = ''
            
            for line in lines:
                if line.startswith('TÍTULO:'):
                    title = line.replace('TÍTULO:', '').strip()
                elif line.startswith('RESUMO:'):
                    summary = line.replace('RESUMO:', '').strip()
                    
            return {
                'title': title[:60],  # Limita tamanho SEO
                'summary': summary[:160]
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar título/resumo: {e}")
            return {'title': 'Título não disponível', 'summary': 'Resumo não disponível'}