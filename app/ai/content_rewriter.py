from typing import Dict, Any, Optional
import google.generativeai as genai
from loguru import logger
from app.core.config import settings

class ContentRewriter:
    """
    Responsável pela reescrita inteligente de conteúdo usando Google Gemini.
    Versão stateless simplificada.
    """
    
    def __init__(self):
        self.gemini_client = None
        
        # Inicializa cliente Google Gemini
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            # Usando o nome correto do modelo disponível
            self.gemini_client = genai.GenerativeModel('gemini-flash-latest')
        else:
            logger.warning("Google API Key não configurada - ContentRewriter sem IA")
    
    async def rewrite_content(self, 
                            original_content: str,
                            persona: str,
                            category: str,
                            target_length: str = "medium") -> Dict[str, Any]:
        """
        Reescreve o conteúdo mantendo a informação mas criando texto original.
        """
        try:
            if not self.gemini_client:
                return self._fallback_rewrite(original_content, persona)
            
            prompt = self._build_rewrite_prompt(original_content, persona, category, target_length)
            rewritten_content = await self._rewrite_with_gemini(prompt)
            
            # Parse o conteúdo estruturado retornado pelo Gemini
            parsed_content = self._parse_rewritten_content(rewritten_content, original_content)
            
            return {
                "title": parsed_content["title"],
                "content": parsed_content["content"],
                "summary": parsed_content["summary"],
                "keywords": parsed_content["keywords"],
                "meta_description": parsed_content["meta_description"],
                "original_length": len(original_content),
                "rewritten_length": len(parsed_content["content"]),
                "persona_used": persona,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Erro na reescrita: {e}")
            return self._fallback_rewrite(original_content, persona)
    
    async def _rewrite_with_gemini(self, prompt: str) -> str:
        """Reescreve usando Google Gemini."""
        try:
            response = self.gemini_client.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Erro com Gemini API: {e}")
            raise
    
    def _build_rewrite_prompt(self, content: str, persona: str, category: str, target_length: str) -> str:
        """Constrói o prompt para reescrita."""
        persona_config = settings.PERSONAS.get(persona, settings.PERSONAS["games"])
        
        length_instructions = {
            "short": "Seja conciso, máximo 2-3 parágrafos.",
            "medium": "Desenvolva bem o tema, 4-6 parágrafos.",
            "long": "Faça análise completa e detalhada."
        }
        
        return f"""
        Reescreva completamente o seguinte conteúdo sobre {category} no formato JSON estruturado.
        
        Estilo: {persona_config['tone']}
        Linguagem: {persona_config['style']}
        Foco: {persona_config['focus']}
        Tamanho: {length_instructions.get(target_length, length_instructions["medium"])}
        
        Conteúdo original:
        {content}
        
        IMPORTANTE: 
        - Mantenha todas as informações factuais
        - Use suas próprias palavras completamente
        - Adapte o tom para o público brasileiro
        - Seja original e criativo
        
        Responda APENAS com um JSON válido no seguinte formato:
        {{
            "title": "Título reescrito e otimizado para SEO",
            "content": "Conteúdo completo reescrito",
            "summary": "Resumo em 2-3 frases",
            "keywords": ["palavra1", "palavra2", "palavra3"],
            "meta_description": "Meta descrição para SEO (max 160 caracteres)"
        }}
        """
    
    def _parse_rewritten_content(self, rewritten_content: str, original_content: str) -> Dict[str, Any]:
        """Parse o conteúdo JSON retornado pelo Gemini."""
        try:
            import json
            import re
            
            # Remove markdown code blocks se existirem
            cleaned_content = re.sub(r'```json\n?|```\n?', '', rewritten_content.strip())
            
            parsed = json.loads(cleaned_content)
            
            # Validação básica
            required_fields = ["title", "content", "summary", "keywords", "meta_description"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Campo obrigatório '{field}' não encontrado")
            
            return parsed
            
        except Exception as e:
            logger.error(f"Erro parsing JSON do Gemini: {e}")
            # Fallback: extrai o que conseguir do texto
            return self._extract_fallback_structure(rewritten_content, original_content)
    
    def _extract_fallback_structure(self, content: str, original_content: str) -> Dict[str, Any]:
        """Extrai estrutura básica quando JSON parse falha."""
        lines = content.strip().split('\n')
        
        # Tenta extrair título da primeira linha
        title = lines[0] if lines else original_content.split('\n')[0][:100]
        
        # Remove caracteres de formatação
        title = title.replace('#', '').replace('*', '').strip()
        
        # Se o conteúdo é muito longo, considera todo como conteúdo
        full_content = '\n'.join(lines[1:]) if len(lines) > 1 else content
        
        words = full_content.split()
        summary = ' '.join(words[:30]) + "..." if len(words) > 30 else full_content
        
        return {
            "title": title[:200],
            "content": full_content,
            "summary": summary[:300],
            "keywords": ["anime", "manga", "games", "noticias"],
            "meta_description": summary[:160]
        }
    
    def _fallback_rewrite(self, content: str, persona: str) -> Dict[str, Any]:
        """Fallback quando IA não está disponível."""
        # Reescrita básica sem IA
        words = content.split()
        title = content.split('\n')[0][:100] if '\n' in content else content[:100]
        
        if len(words) > 100:
            content_text = " ".join(words[:100]) + "..."
        else:
            content_text = content
            
        summary = content_text[:200] + "..." if len(content_text) > 200 else content_text
        
        return {
            "title": f"[{persona.upper()}] {title}",
            "content": content_text,
            "summary": summary,
            "keywords": ["anime", "manga", "games"],
            "meta_description": summary[:160],
            "original_length": len(content),
            "rewritten_length": len(content_text),
            "persona_used": persona,
            "success": False,
            "fallback": True
        }