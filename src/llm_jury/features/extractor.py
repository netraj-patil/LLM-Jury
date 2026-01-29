"""
Feature Extraction Logic.
Transforms raw text into predictive features (counts, complexity, density) as per FR 1.1.
"""

import re
import math
import zlib
from typing import Dict, Any
from collections import Counter

class FeatureExtractor:
    """
    Analyzes text to extract quantitative features for the Jury Manifest.
    Implements the feature extraction logic defined in the Class Diagram and Requirements.
    """

    def extract_text_metrics(self, text: str) -> Dict[str, Any]:
        """
        Calculates basic structural metrics of the text.
        
        Metrics:
        - Word Count, Character Count, Sentence Count.
        - Paragraph Count.
        - Compression Ratio (Intrinsic): A measure of information density using zlib.
        
        Args:
            text (str): The string to analyze.

        Returns:
            Dict[str, Any]: A dictionary of calculated text features.
        """
        if not text:
            return {
                "char_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "compression_ratio": 0.0
            }

        # Basic Counts
        char_count = len(text)
        words = re.findall(r'\b\w+\b', text.lower())
        word_count = len(words)
        
        # approximate sentence count using punctuation
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()] # Filter empty
        sentence_count = len(sentences)
        
        # Paragraphs usually separated by double newlines
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)

        # Intrinsic Compression Ratio (Zlib size / Raw size)
        # Represents information density/redundancy 
        # Lower ratio = highly compressible (redundant/simple)
        # Higher ratio = high entropy (dense/complex)
        compressed_data = zlib.compress(text.encode('utf-8'))
        compression_ratio = len(compressed_data) / char_count if char_count > 0 else 0.0

        return {
            "char_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "compression_ratio": round(compression_ratio, 4)
        }

    def extract_complexity(self, text: str) -> Dict[str, Any]:
        """
        Calculates linguistic complexity metrics.
        
        Metrics:
        - Flesch Reading Ease: Standard readability formula.
        - Avg Sentence Length: syntactic complexity proxy.
        - Type-Token Ratio (TTR): Lexical diversity measure.
        
        Args:
            text (str): The string to analyze.

        Returns:
            Dict[str, Any]: Complexity scores.
        """
        if not text:
            return {"flesch_reading_ease": 0.0, "lexical_diversity": 0.0}

        # Pre-calc required stats
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        total_sentences = len([s for s in re.split(r'[.!?]+', text) if s.strip()])
        
        if total_words == 0 or total_sentences == 0:
            return {"flesch_reading_ease": 0.0, "lexical_diversity": 0.0}

        # Syllable approximation for Flesch Score
        total_syllables = sum(self._count_syllables(w) for w in words)

        # Flesch Reading Ease Formula: 
        # 206.835 - 1.015(total_words/total_sentences) - 84.6(total_syllables/total_words)
        avg_sentence_len = total_words / total_sentences
        avg_syllables_per_word = total_syllables / total_words
        
        flesch_score = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables_per_word)

        # Lexical Diversity (Type-Token Ratio)
        unique_words = set(words)
        ttr = len(unique_words) / total_words if total_words > 0 else 0.0

        return {
            "flesch_reading_ease": round(flesch_score, 2),
            "lexical_diversity": round(ttr, 4),
            "avg_sentence_length": round(avg_sentence_len, 2)
        }
    
    def extract_special_words(self, text: str) -> Dict[str, Any]:
        words = re.findall(r'\b\w+\b', text.lower())

        # Difficult words (3+ syllables)
        difficult_words = [w for w in words if self._count_syllables(w) >= 3]

        # Modality verbs
        modality_verbs = ['can', 'could', 'may', 'might', 'must', 'shall', 
                          'should', 'will', 'would']
        modality_count = sum(1 for w in words if w in modality_verbs)

        # Shannon entropy
        word_freq = Counter(words)
        total = len(words)
        entropy = -sum((count/total) * math.log2(count/total) 
                       for count in word_freq.values() if count > 0)

        return {
            "difficult_word_count": len(difficult_words),
            "modality_verb_count": modality_count,
            "shannon_entropy": round(entropy, 4)
        }

    def _count_syllables(self, word: str) -> int:
        """Heuristic to count syllables in a word for readability scoring."""
        word = word.lower()
        count = 0
        vowels = "aeiou"
        if len(word) == 0:
            return 0
        if word[0] in vowels:
            count += 1
        for i in range(1, len(word)):
            if word[i] in vowels and word[i - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count = 1
        return count