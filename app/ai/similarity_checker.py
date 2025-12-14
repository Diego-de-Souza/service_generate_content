from typing import List, Tuple
import re
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from loguru import logger

class SimilarityChecker:
    """
    Verifica similaridade entre textos para garantir originalidade.
    Usa múltiplas métricas para detectar plágio potencial.
    """
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words=None,  # Não remove stop words em português
            max_features=5000,
            ngram_range=(1, 3),  # Usa unigramas, bigramas e trigramas
            min_df=1
        )
        
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridade entre dois textos usando múltiplas métricas.
        
        Args:
            text1: Primeiro texto (geralmente o original)
            text2: Segundo texto (geralmente o reescrito)
            
        Returns:
            Score de similaridade (0-1, onde 1 é idêntico)
        """
        try:
            # Pré-processa textos
            clean_text1 = self._preprocess_text(text1)
            clean_text2 = self._preprocess_text(text2)
            
            # Calcula diferentes métricas
            sequence_similarity = self._calculate_sequence_similarity(clean_text1, clean_text2)
            tfidf_similarity = self._calculate_tfidf_similarity(clean_text1, clean_text2)
            phrase_similarity = self._calculate_phrase_similarity(text1, text2)
            
            # Combina métricas com pesos
            final_similarity = (
                sequence_similarity * 0.3 +
                tfidf_similarity * 0.4 +
                phrase_similarity * 0.3
            )
            
            logger.info(
                f"Similarity scores - Sequence: {sequence_similarity:.3f}, "
                f"TF-IDF: {tfidf_similarity:.3f}, Phrase: {phrase_similarity:.3f}, "
                f"Final: {final_similarity:.3f}"
            )
            
            return final_similarity
            
        except Exception as e:
            logger.error(f"Erro ao calcular similaridade: {e}")
            return 0.5  # Retorna valor neutro em caso de erro
            
    def _preprocess_text(self, text: str) -> str:
        """
        Pré-processa texto para análise de similaridade.
        """
        # Remove caracteres especiais mas mantém acentos
        text = re.sub(r'[^\w\sáàâãéèêíìîóòôõúùûç]', ' ', text.lower())
        
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def _calculate_sequence_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridade usando SequenceMatcher (algoritmo de diff).
        """
        try:
            matcher = SequenceMatcher(None, text1, text2)
            return matcher.ratio()
        except Exception:
            return 0.0
            
    def _calculate_tfidf_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridade usando TF-IDF e cosine similarity.
        """
        try:
            # Cria corpus com os dois textos
            corpus = [text1, text2]
            
            # Vetoriza textos
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Calcula cosine similarity
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return cosine_sim
            
        except Exception as e:
            logger.error(f"Erro no cálculo TF-IDF: {e}")
            return 0.0
            
    def _calculate_phrase_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridade baseada em frases comuns.
        """
        try:
            # Divide em frases
            sentences1 = self._extract_sentences(text1)
            sentences2 = self._extract_sentences(text2)
            
            if not sentences1 or not sentences2:
                return 0.0
                
            # Conta frases similares
            similar_count = 0
            total_comparisons = 0
            
            for sent1 in sentences1:
                for sent2 in sentences2:
                    if len(sent1) > 20 and len(sent2) > 20:  # Ignora frases muito curtas
                        total_comparisons += 1
                        # Usa SequenceMatcher para frases individuais
                        similarity = SequenceMatcher(None, sent1.lower(), sent2.lower()).ratio()
                        if similarity > 0.8:  # Frases muito similares
                            similar_count += 1
                            
            if total_comparisons == 0:
                return 0.0
                
            return similar_count / total_comparisons
            
        except Exception as e:
            logger.error(f"Erro no cálculo de frases: {e}")
            return 0.0
            
    def _extract_sentences(self, text: str) -> List[str]:
        """
        Extrai frases do texto.
        """
        # Split por pontuação de fim de frase
        sentences = re.split(r'[.!?]+', text)
        
        # Limpa e filtra frases
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Ignora frases muito curtas
                cleaned_sentences.append(sentence)
                
        return cleaned_sentences
        
    def detect_plagiarism(self, original: str, rewritten: str, threshold: float = 0.7) -> dict:
        """
        Detecta possível plágio comparando textos.
        
        Args:
            original: Texto original
            rewritten: Texto reescrito
            threshold: Limite para considerar plágio (padrão: 0.7)
            
        Returns:
            Dict com resultado da análise
        """
        similarity_score = self.calculate_similarity(original, rewritten)
        
        result = {
            'similarity_score': similarity_score,
            'is_plagiarism': similarity_score > threshold,
            'risk_level': self._get_risk_level(similarity_score),
            'recommendations': self._get_recommendations(similarity_score)
        }
        
        return result
        
    def _get_risk_level(self, similarity: float) -> str:
        """
        Determina nível de risco baseado na similaridade.
        """
        if similarity >= 0.8:
            return 'ALTO - Possível plágio'
        elif similarity >= 0.6:
            return 'MÉDIO - Reescrita insuficiente'
        elif similarity >= 0.4:
            return 'BAIXO - Similaridade aceitável'
        else:
            return 'MÍNIMO - Conteúdo original'
            
    def _get_recommendations(self, similarity: float) -> List[str]:
        """
        Gera recomendações baseadas no score de similaridade.
        """
        recommendations = []
        
        if similarity >= 0.8:
            recommendations.extend([
                "Reescreva completamente o conteúdo",
                "Mude a estrutura narrativa",
                "Use sinônimos e expressões diferentes",
                "Adicione análise e contexto próprio"
            ])
        elif similarity >= 0.6:
            recommendations.extend([
                "Modifique mais parágrafos",
                "Varie o vocabulário usado",
                "Reorganize as informações",
                "Adicione insights editoriais"
            ])
        elif similarity >= 0.4:
            recommendations.extend([
                "Bom nível de originalidade",
                "Considere adicionar mais contexto próprio",
                "Verifique se manteve as informações factuais"
            ])
        else:
            recommendations.append("Excelente originalidade!")
            
        return recommendations
        
    def find_similar_phrases(self, text1: str, text2: str, min_length: int = 5) -> List[Tuple[str, float]]:
        """
        Encontra frases similares entre dois textos.
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
            min_length: Tamanho mínimo da frase em palavras
            
        Returns:
            Lista de tuplas (frase, score_similaridade)
        """
        sentences1 = self._extract_sentences(text1)
        sentences2 = self._extract_sentences(text2)
        
        similar_phrases = []
        
        for sent1 in sentences1:
            words1 = sent1.split()
            if len(words1) < min_length:
                continue
                
            for sent2 in sentences2:
                words2 = sent2.split()
                if len(words2) < min_length:
                    continue
                    
                similarity = SequenceMatcher(None, sent1.lower(), sent2.lower()).ratio()
                
                if similarity > 0.7:  # Threshold para frases similares
                    similar_phrases.append((sent1, similarity))
                    
        # Ordena por similaridade
        similar_phrases.sort(key=lambda x: x[1], reverse=True)
        
        return similar_phrases
        
    def batch_similarity_check(self, target_text: str, reference_texts: List[str]) -> Dict[str, float]:
        """
        Verifica similaridade do texto alvo contra múltiplos textos de referência.
        
        Args:
            target_text: Texto a ser verificado
            reference_texts: Lista de textos de referência
            
        Returns:
            Dict com scores de similaridade para cada referência
        """
        results = {}
        
        for i, ref_text in enumerate(reference_texts):
            similarity = self.calculate_similarity(target_text, ref_text)
            results[f'reference_{i}'] = similarity
            
        return results