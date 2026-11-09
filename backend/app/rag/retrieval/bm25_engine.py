import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("convelina.rag.bm25")

class BM25Engine:
    """
    Production-grade Okapi BM25 Lexical Ranking Engine for CONVELINA official legal corpus.
    Parameters:
      k1 = 1.5 (term frequency saturation)
      b = 0.75 (document length penalization)
    Supports tokenization with Unicode/Indic support and category/provenance pre-filtering.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[Dict[str, Any]] = []
        self.doc_tokens: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avgdl: float = 0.0
        self.idf: Dict[str, float] = {}
        self.doc_freqs: Dict[str, int] = {}
        self.n_docs: int = 0
        self._is_indexed: bool = False

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenizes text into normalized lowercased terms.
        Supports standard alphanumeric and Tamil/Indic Unicode codepoints (\u0B80-\u0BFF).
        """
        if not text:
            return []
        tokens = re.findall(r'[\w\u0B80-\u0BFF]{2,}', text.lower())
        return tokens

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """Indexes a list of chunks, building IDF and length statistics."""
        self.chunks = chunks
        self.n_docs = len(chunks)
        self.doc_tokens = []
        self.doc_lengths = []
        self.doc_freqs = {}

        if self.n_docs == 0:
            self.avgdl = 0.0
            self.idf = {}
            self._is_indexed = True
            return

        total_length = 0
        for chunk in self.chunks:
            # We index both chunk_text and section_title/document_title for rich lexical matching
            text_to_index = f"{chunk.get('document_title', '')} {chunk.get('section_title', '')} {chunk.get('chunk_text', '')}"
            tokens = self.tokenize(text_to_index)
            self.doc_tokens.append(tokens)
            dl = len(tokens)
            self.doc_lengths.append(dl)
            total_length += dl

            seen_terms = set(tokens)
            for term in seen_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avgdl = total_length / max(1, self.n_docs)

        # Standard Lucene/BM25 formula with smoothing
        self.idf = {}
        for term, df in self.doc_freqs.items():
            self.idf[term] = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1.0)

        self._is_indexed = True
        logger.info("BM25Engine indexed %d chunks (avgdl=%.1f, vocab=%d)", self.n_docs, self.avgdl, len(self.idf))

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_category: Optional[str] = None,
        corpus_classification: Optional[str] = None,
        min_score: float = 0.0,
        min_coverage: float = 0.34
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Scores all indexed chunks against query with optional category / classification filters.
        Enforces query term coverage to prevent distractor traps and false positive matches.
        Returns top_k tuples of (score, chunk_dict).
        """
        if not self._is_indexed or self.n_docs == 0:
            return []

        q_tokens = self.tokenize(query)
        if not q_tokens:
            return []

        stop_words = {"how", "do", "i", "my", "the", "in", "a", "an", "is", "for", "to", "what", "which", "and", "or", "of", "can", "according"}
        informative_q_tokens = [w for w in q_tokens if w not in stop_words]
        if not informative_q_tokens:
            informative_q_tokens = q_tokens

        scored_results: List[Tuple[float, Dict[str, Any]]] = []

        cat_filter = document_category.lower() if document_category else None
        class_filter = corpus_classification.upper() if corpus_classification else None

        for idx, chunk in enumerate(self.chunks):
            # Pre-filtering
            if cat_filter and chunk.get("document_category", "").lower() != cat_filter:
                continue
            if class_filter and chunk.get("corpus_classification", "").upper() != class_filter:
                continue

            tokens = self.doc_tokens[idx]
            dl = self.doc_lengths[idx]
            if dl == 0:
                continue

            # Term frequency in document
            tf_map: Dict[str, int] = {}
            for t in tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            # Check coverage of informative query terms
            matched_inf = sum(1 for qt in informative_q_tokens if qt in tf_map)
            coverage = matched_inf / max(1, len(informative_q_tokens))
            if coverage < min_coverage:
                continue

            score = 0.0
            for qt in q_tokens:
                if qt in tf_map:
                    tf = tf_map[qt]
                    term_idf = self.idf.get(qt, 0.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (dl / self.avgdl))
                    term_score = term_idf * (tf * (self.k1 + 1.0)) / denominator
                    score += term_score

            if score >= min_score and score > 0.0:
                scored_results.append((round(score, 4), chunk))

        # Sort descending by score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return scored_results[:top_k]
