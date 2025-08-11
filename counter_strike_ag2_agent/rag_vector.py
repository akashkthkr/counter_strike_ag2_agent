from __future__ import annotations

from typing import List, Optional

import chromadb
from chromadb.utils import embedding_functions


class ChromaRAG:
    """Tiny wrapper around ChromaDB for Q&A.

    Commands supported (see multi_main wiring):
    - kb:load <path>   -> load a text file into the shared collection
    - kb:add <text>    -> add a single text snippet
    - ask: <question>  -> semantic search + return top-1 chunk as answer
    """

    def __init__(self, persist_dir: str = ".chroma", collection: str = "cs_kb") -> None:
        self.client = chromadb.PersistentClient(path=persist_dir)
        # Use OpenAI embedding if env is present, else default sentence-transformers
        try:
            ef = embedding_functions.OpenAIEmbeddingFunction()
        except Exception:
            ef = embedding_functions.DefaultEmbeddingFunction()
        self.col = self.client.get_or_create_collection(collection, embedding_function=ef)

    def add_texts(self, texts: List[str]) -> int:
        ids = [f"doc-{self.col.count()}-{i}" for i in range(len(texts))]
        self.col.add(documents=texts, ids=ids)
        return len(texts)

    def add_file(self, path: str) -> int:
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError:
            return 0
        # naive split to paragraphs
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
        return self.add_texts(chunks)

    def ask(self, question: str) -> Optional[str]:
        question = question.strip()
        if not question:
            return None
        res = self.col.query(query_texts=[question], n_results=1)
        try:
            return res["documents"][0][0]
        except Exception:
            return None


