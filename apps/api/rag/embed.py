import os
import math
import re
from typing import List

class EmbeddingModel:
    """
    Embedding helper wrapper. Uses ChromaDB default or semantic vectorizer.
    """
    def __init__(self):
        self.dim = 384

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # ChromaDB has internal default embeddings, this is for custom vector calculations
        vectors = []
        for text in texts:
            vectors.append(self._vectorize(text))
        return vectors

    def embed_query(self, text: str) -> List[float]:
        return self._vectorize(text)

    def _vectorize(self, text: str) -> List[float]:
        tokens = re.findall(r"\w+", text.lower())
        vec = [0.0] * self.dim
        if not tokens:
            return vec
        for token in tokens:
            h = hash(token) % self.dim
            vec[h] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

embedding_model = EmbeddingModel()
