from dataclasses import dataclass
import math
import re

import numpy as np

from app.core.config import get_settings
from app.services.transcripts import TranscriptChunk


@dataclass
class SearchResult:
    chunk: TranscriptChunk
    score: float


class RagIndex:
    def __init__(self, chunks: list[TranscriptChunk]) -> None:
        self.chunks = chunks
        self._model = None
        self._embeddings: np.ndarray | None = None
        self._load_embeddings()

    def search(self, query: str, top_k: int = 4) -> list[SearchResult]:
        if self._model is not None and self._embeddings is not None:
            return self._semantic_search(query, top_k)

        return self._keyword_search(query, top_k)

    def _load_embeddings(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            settings = get_settings()
            self._model = SentenceTransformer(settings.embedding_model)
            vectors = self._model.encode(
                [chunk.text for chunk in self.chunks],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            self._embeddings = np.asarray(vectors)
        except Exception:
            self._model = None
            self._embeddings = None

    def _semantic_search(self, query: str, top_k: int) -> list[SearchResult]:
        query_vector = self._model.encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        )[0]
        scores = np.dot(self._embeddings, query_vector)
        ranked_indexes = np.argsort(scores)[::-1][:top_k]

        return [
            SearchResult(chunk=self.chunks[index], score=float(scores[index]))
            for index in ranked_indexes
        ]

    def _keyword_search(self, query: str, top_k: int) -> list[SearchResult]:
        query_terms = _tokenize(query)
        results: list[SearchResult] = []

        for chunk in self.chunks:
            chunk_terms = _tokenize(chunk.text)
            overlap = query_terms.intersection(chunk_terms)
            score = len(overlap) / math.sqrt(max(len(chunk_terms), 1))
            results.append(SearchResult(chunk=chunk, score=score))

        return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]


def _tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", value.lower())
        if len(token) > 2
    }

