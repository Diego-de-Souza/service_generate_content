from typing import Dict, List, Any, Optional
import re
from slugify import slugify
from app.core.config import settings

class SEOOptimizer:
    """
    Otimiza conteúdo para SEO de forma automática.
    """
    
    def __init__(self):
        self.stop_words = [
            'a', 'o', 'e', 'de', 'do', 'da', 'em', 'um', 'uma', 'para', 'com', 'por', 
            'ao', 'dos', 'das', 'na', 'no', 'se', 'que', 'não', 'mais', 'como', 'mas',
            'já', 'até', 'ou', 'sua', 'seu', 'ela', 'ele', 'eles', 'elas', 'isso', 'esta',
            'este', 'essa', 'esse', 'são', 'foi', 'ser', 'ter', 'seu', 'seus', 'duas'
        ]
        
    def optimize_content(self, 
                       title: str, 
                       content: str, 
                       category: str,
                       target_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Otimiza título, conteúdo e metadados para SEO.
        
        Args:
            title: Título do artigo
            content: Conteúdo do artigo
            category: Categoria do conteúdo
            target_keywords: Lista de palavras-chave alvo (opcional)
            
        Returns:
            Dict com dados otimizados para SEO
        """
        # Extrai palavras-chave se não fornecidas
        if not target_keywords:
            target_keywords = self.extract_keywords(content, max_keywords=10)
            
        # Otimiza título
        optimized_title = self.optimize_title(title, target_keywords[:3])
        
        # Gera slug
        slug = self.generate_slug(optimized_title)
        
        # Gera meta description
        meta_description = self.generate_meta_description(content, target_keywords[:2])
        
        # Otimiza conteúdo
        optimized_content = self.optimize_content_structure(content, target_keywords)
        
        # Gera dados estruturados
        structured_data = self.generate_structured_data(
            optimized_title, meta_description, category, slug
        )
        
        return {
            'title': optimized_title,
            'slug': slug,
            'meta_title': optimized_title[:60],  # Limite do Google
            'meta_description': meta_description,
            'keywords': target_keywords,
            'optimized_content': optimized_content,
            'structured_data': structured_data,
            'seo_score': self.calculate_seo_score(
                optimized_title, optimized_content, meta_description, target_keywords
            )
        }
        
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """
        Extrai palavras-chave relevantes do conteúdo.
        """
        # Remove pontuação e converte para minúsculas
        text = re.sub(r'[^\w\s]', '', content.lower())
        
        # Divide em palavras
        words = text.split()
        
        # Remove stop words
        filtered_words = [word for word in words if word not in self.stop_words and len(word) > 3]
        
        # Conta frequência
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
            
        # Ordena por frequência
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Retorna top keywords
        return [word for word, freq in sorted_words[:max_keywords] if freq > 1]
        
    def optimize_title(self, title: str, primary_keywords: List[str]) -> str:
        """
        Otimiza título para SEO mantendo atratividade.
        """
        optimized = title.strip()
        
        # Garante que pelo menos uma keyword primária está no título
        has_keyword = any(keyword.lower() in optimized.lower() for keyword in primary_keywords[:2])
        
        if not has_keyword and primary_keywords:
            # Adiciona keyword principal de forma natural
            if len(optimized) + len(primary_keywords[0]) + 3 <= 60:
                optimized = f"{primary_keywords[0].title()}: {optimized}"
                
        # Garante tamanho adequado
        if len(optimized) > 60:
            optimized = optimized[:57] + "..."
            
        return optimized
        
    def generate_slug(self, title: str) -> str:
        """
        Gera slug SEO-friendly a partir do título.
        """
        return slugify(title, max_length=50)
        
    def generate_meta_description(self, content: str, keywords: List[str]) -> str:
        """
        Gera meta description otimizada.
        """
        # Pega as primeiras frases do conteúdo
        sentences = content.split('. ')[:3]
        description = '. '.join(sentences)
        
        # Garante que keywords estão incluídas
        for keyword in keywords[:2]:
            if keyword.lower() not in description.lower() and len(description) + len(keyword) + 2 <= 160:
                description += f" {keyword.title()}."
                
        # Limita tamanho
        if len(description) > 160:
            description = description[:157] + "..."
            
        return description
        
    def optimize_content_structure(self, content: str, keywords: List[str]) -> str:
        """
        Otimiza estrutura do conteúdo para SEO.
        """
        paragraphs = content.split('\n\n')
        optimized_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            # Primeiro parágrafo deve conter keyword principal
            if i == 0 and keywords:
                if keywords[0].lower() not in paragraph.lower():
                    # Tenta inserir naturalmente
                    words = paragraph.split()
                    if len(words) > 10:
                        insertion_point = len(words) // 3
                        words.insert(insertion_point, keywords[0])
                        paragraph = ' '.join(words)
                        
            optimized_paragraphs.append(paragraph)
            
        # Adiciona subtítulos se não existirem
        if len(optimized_paragraphs) > 3 and not any('#' in p for p in optimized_paragraphs):
            # Adiciona subtítulos baseados em keywords
            for i in range(1, len(optimized_paragraphs), 2):
                if i < len(keywords) + 1:
                    subtitle = f"\n## {keywords[i-1].title()}"
                    optimized_paragraphs.insert(i, subtitle)
                    
        return '\n\n'.join(optimized_paragraphs)
        
    def generate_structured_data(self, title: str, description: str, category: str, slug: str) -> Dict[str, Any]:
        """
        Gera dados estruturados JSON-LD para o artigo.
        """
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "articleSection": category,
            "url": f"/{slug}",
            "datePublished": None,  # Será preenchido quando publicado
            "dateModified": None,
            "author": {
                "@type": "Organization",
                "name": "Plataforma Geek"
            },
            "publisher": {
                "@type": "Organization", 
                "name": "Plataforma Geek",
                "logo": {
                    "@type": "ImageObject",
                    "url": "/logo.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"/{slug}"
            }
        }
        
    def calculate_seo_score(self, title: str, content: str, meta_description: str, keywords: List[str]) -> float:
        """
        Calcula score de SEO do conteúdo (0-1).
        """
        score = 0.0
        
        # Título (20%)
        if 30 <= len(title) <= 60:
            score += 0.15
        if keywords and keywords[0].lower() in title.lower():
            score += 0.05
            
        # Meta description (15%)
        if 120 <= len(meta_description) <= 160:
            score += 0.1
        if keywords and any(kw.lower() in meta_description.lower() for kw in keywords[:2]):
            score += 0.05
            
        # Conteúdo (40%)
        word_count = len(content.split())
        if 300 <= word_count <= 2000:
            score += 0.15
            
        # Densidade de keywords (2-4% é ideal)
        if keywords:
            total_words = len(content.split())
            keyword_density = sum(content.lower().count(kw.lower()) for kw in keywords[:3]) / total_words
            if 0.02 <= keyword_density <= 0.04:
                score += 0.1
            elif keyword_density <= 0.06:  # Aceitável
                score += 0.05
                
        # Estrutura (15%)
        if '##' in content or content.count('\n\n') >= 2:  # Tem subtítulos ou parágrafos
            score += 0.1
        if len(content.split('\n\n')) >= 3:  # Boa divisão em parágrafos
            score += 0.05
            
        # Links internos/externos (10%)
        if '[' in content and '](' in content:  # Tem links markdown
            score += 0.1
            
        return min(score, 1.0)
        
    def suggest_improvements(self, title: str, content: str, meta_description: str, keywords: List[str]) -> List[str]:
        """
        Sugere melhorias para otimização SEO.
        """
        suggestions = []
        
        # Análise do título
        if len(title) < 30:
            suggestions.append("Título muito curto. Ideal: 30-60 caracteres.")
        elif len(title) > 60:
            suggestions.append("Título muito longo. Ideal: 30-60 caracteres.")
            
        if keywords and not any(kw.lower() in title.lower() for kw in keywords[:2]):
            suggestions.append(f"Adicione a palavra-chave '{keywords[0]}' no título.")
            
        # Análise da meta description
        if len(meta_description) < 120:
            suggestions.append("Meta description muito curta. Ideal: 120-160 caracteres.")
        elif len(meta_description) > 160:
            suggestions.append("Meta description muito longa. Ideal: 120-160 caracteres.")
            
        # Análise do conteúdo
        word_count = len(content.split())
        if word_count < 300:
            suggestions.append("Conteúdo muito curto. Mínimo recomendado: 300 palavras.")
            
        if '##' not in content and content.count('\n\n') < 2:
            suggestions.append("Adicione subtítulos (##) para melhorar a estrutura.")
            
        # Análise de keywords
        if keywords:
            total_words = len(content.split())
            keyword_density = sum(content.lower().count(kw.lower()) for kw in keywords[:3]) / total_words
            
            if keyword_density < 0.01:
                suggestions.append("Densidade de palavras-chave muito baixa. Inclua mais keywords naturalmente.")
            elif keyword_density > 0.05:
                suggestions.append("Densidade de palavras-chave muito alta. Pode ser considerado spam.")
                
        return suggestions