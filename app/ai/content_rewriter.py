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
            self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
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
            
            return {
                "rewritten_text": rewritten_content,
                "original_length": len(original_content),
                "rewritten_length": len(rewritten_content),
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
        Reescreva completamente o seguinte conteúdo sobre {category}.
        
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
        """
    
    def _fallback_rewrite(self, content: str, persona: str) -> Dict[str, Any]:
        """Fallback quando IA não está disponível."""
        # Reescrita básica sem IA
        words = content.split()
        if len(words) > 100:
            content = " ".join(words[:100]) + "..."
        
        return {
            "rewritten_text": f"[{persona.upper()}] {content}",
            "original_length": len(content),
            "rewritten_length": len(content) + 20,
            "persona_used": persona,
            "success": False,
            "fallback": True
        }