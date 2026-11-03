import os
from dataclasses import dataclass
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings

from src.faq import FaqEntry, load_faq
from src.llm import get_llm

EMBED_MODEL = "bge-m3"
REWRITE_MODEL = os.environ.get("NB_MODEL", "qwen3.5:9b-mlx")  # env override lets eval swap the model
CHROMA_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
COLLECTION = "bank_faq"


@dataclass(frozen=True)
class Hit:
    faq_id: int
    score: float  # cosine similarity, higher is better


@dataclass(frozen=True)
class Retrieval:
    hits: list[Hit]
    rewrite: str | None  # the Bangla search rewrite, shown only for debugging


def _doc_text(e: FaqEntry) -> str:
    # Question plus answer: customers often use words that only appear in the answer.
    return f"{e.topic}: {e.question}\n{e.answer}"


class Retriever:
    def __init__(self, faq: list[FaqEntry] | None = None):
        self.faq = faq or load_faq()
        # Rebuild every start: only 30 entries, and it avoids a stale index after FAQ edits.
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
        # LangChain's Chroma store plus Ollama embeddings (bge-m3). Cosine, same as before.
        self.store = Chroma(collection_name=COLLECTION, client=client,
                            embedding_function=OllamaEmbeddings(model=EMBED_MODEL),
                            collection_metadata={"hnsw:space": "cosine"})
        self.store.add_documents(
            [Document(page_content=_doc_text(e),
                      metadata={"faq_id": e.id, "topic": e.topic, "question": e.question,
                                "answer": e.answer}) for e in self.faq],
            ids=[str(e.id) for e in self.faq])

    def search(self, query: str, k: int = 3) -> list[Hit]:
        # Chroma returns a cosine distance (lower is better), so score = 1 - distance.
        found = self.store.similarity_search_with_score(query, k=k)
        return [Hit(int(doc.metadata["faq_id"]), 1 - dist) for doc, dist in found]

    def retrieve(self, question: str, lang: str, k: int = 3) -> "Retrieval":
        """Option C. Banglish: search with the original AND a Bangla rewrite, keep the best
        score per FAQ entry. Other languages: plain search."""
        if lang != "banglish":
            return Retrieval(self.search(question, k), None)
        try:
            rewrite = rewrite_query(question, "bangla")
        except Exception:
            # A failed rewrite must not break the reply. The original question still works.
            return Retrieval(self.search(question, k), None)
        n = len(self.faq)
        return Retrieval(merge_best(self.search(question, n), self.search(rewrite, n))[:k], rewrite)


REWRITE_PROMPTS = {
    "english": "Translate this bank customer question, written in Banglish (Bangla in English "
               "letters), into plain English. Output only the translation.\n\nQuestion: {q}",
    "bangla": "Translate this bank customer question, written in Banglish (Bangla in English "
              "letters), into Bangla script. Output only the translation.\n\nQuestion: {q}",
}


def rewrite_query(question: str, target: str) -> str:
    """Rewrite a banglish question for SEARCH ONLY. The reply language is never affected."""
    chain = (ChatPromptTemplate.from_template(REWRITE_PROMPTS[target])
             | get_llm(REWRITE_MODEL) | StrOutputParser())
    return chain.invoke({"q": question}).strip()


def merge_best(*hit_lists: list[Hit]) -> list[Hit]:
    """Combine several searches: each FAQ entry keeps its best score, then sort."""
    best: dict[int, float] = {}
    for hits in hit_lists:
        for h in hits:
            best[h.faq_id] = max(best.get(h.faq_id, -1.0), h.score)
    return sorted((Hit(i, s) for i, s in best.items()), key=lambda h: -h.score)
