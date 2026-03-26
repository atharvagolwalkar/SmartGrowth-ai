"""
Semantic Search Engine — SmartGrowth AI NLP Module

Uses sentence-transformers to embed customer feedback and ChromaDB
as the vector store. Enables meaning-based search — finding "billing
problem" returns "charged twice", "wrong invoice", "unexpected fee"
even with zero keyword overlap.

Model: all-MiniLM-L6-v2 (22MB, fast, production-quality)
  - 384-dimensional embeddings
  - Trained on 1B+ sentence pairs
  - ~14k sentences/sec on CPU

ChromaDB: embedded (no server needed), persists to disk.

Usage:
    engine = SemanticSearchEngine()
    engine.build_index(feedback_df)           # one-time setup
    results = engine.search("billing issue", top_k=5)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_DEFAULT_MODEL   = "all-MiniLM-L6-v2"
_DEFAULT_DB_PATH = str(Path(__file__).resolve().parent / "artifacts" / "chroma_db")
_COLLECTION_NAME = "customer_feedback"


class SemanticSearchEngine:
    """
    Semantic search over customer feedback using embeddings + ChromaDB.

    Falls back to TF-IDF keyword search if sentence-transformers
    or ChromaDB are not installed — so the dashboard always works.
    """

    def __init__(
        self,
        model_name: str = _DEFAULT_MODEL,
        db_path: str = _DEFAULT_DB_PATH,
    ):
        self.model_name = model_name
        self.db_path    = db_path
        self.model      = None
        self.client     = None
        self.collection = None
        self.backend    = "none"
        self._fallback_df:    Optional[pd.DataFrame] = None
        self._fallback_tfidf  = None
        self._fallback_matrix = None

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _init_backend(self) -> str:
        try:
            from sentence_transformers import SentenceTransformer  # noqa
            import chromadb                                          # noqa
            return "chromadb"
        except ImportError:
            pass
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # noqa
            return "tfidf"
        except ImportError:
            pass
        return "none"

    def _load_model(self) -> None:
        if self.model is not None:
            return
        logger.info(f"Loading embedding model: {self.model_name}")
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(self.model_name)
        logger.info("Embedding model loaded.")

    def _init_chroma(self) -> None:
        import chromadb
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Index building ────────────────────────────────────────────────────────

    def build_index(self, df: pd.DataFrame, batch_size: int = 64) -> "SemanticSearchEngine":
        """
        Embed all feedback texts and store in ChromaDB (or TF-IDF fallback).

        df must have columns: feedback_id, feedback_text, and optionally
        customer_id, category, sentiment_label, sentiment_score, created_at, channel.
        """
        self.backend = self._init_backend()
        logger.info(f"NLP backend: {self.backend}")

        if self.backend == "chromadb":
            self._build_chromadb_index(df, batch_size)
        elif self.backend == "tfidf":
            self._build_tfidf_index(df)
        else:
            logger.warning("No NLP backend available. Install sentence-transformers + chromadb.")
            self._fallback_df = df.copy()

        return self

    def _build_chromadb_index(self, df: pd.DataFrame, batch_size: int) -> None:
        self._load_model()
        self._init_chroma()

        # Clear existing and rebuild
        try:
            self.client.delete_collection(_COLLECTION_NAME)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        texts = df["feedback_text"].tolist()
        ids   = df["feedback_id"].tolist()

        # Build metadata dicts
        meta_cols = ["customer_id", "category", "sentiment_label",
                     "sentiment_score", "channel", "created_at"]
        metadatas = []
        for _, row in df.iterrows():
            m = {}
            for col in meta_cols:
                if col in df.columns:
                    val = row[col]
                    # ChromaDB only accepts str/int/float/bool
                    if pd.isna(val) if not isinstance(val, str) else False:
                        m[col] = ""
                    elif hasattr(val, 'item'):
                        m[col] = val.item()
                    else:
                        m[col] = str(val) if not isinstance(val, (int, float, bool)) else val
            metadatas.append(m)

        logger.info(f"Embedding {len(texts)} feedback records in batches of {batch_size}...")
        for start in range(0, len(texts), batch_size):
            batch_texts = texts[start:start + batch_size]
            batch_ids   = ids[start:start + batch_size]
            batch_meta  = metadatas[start:start + batch_size]

            embeddings = self.model.encode(
                batch_texts,
                show_progress_bar=False,
                convert_to_numpy=True,
            ).tolist()

            self.collection.add(
                ids=batch_ids,
                documents=batch_texts,
                embeddings=embeddings,
                metadatas=batch_meta,
            )

        logger.info(f"Index built: {self.collection.count()} documents.")

    def _build_tfidf_index(self, df: pd.DataFrame) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._fallback_df = df.copy()
        self._fallback_tfidf = TfidfVectorizer(
            max_features=5000, stop_words="english", ngram_range=(1, 2)
        )
        self._fallback_matrix = self._fallback_tfidf.fit_transform(
            df["feedback_text"].tolist()
        )
        logger.info(f"TF-IDF fallback index built: {len(df)} documents.")

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_sentiment: Optional[str] = None,   # "positive" | "negative" | "neutral"
        filter_category:  Optional[str] = None,
    ) -> list[dict]:
        """
        Search feedback semantically.

        Returns list of dicts with:
            feedback_id, feedback_text, similarity_score,
            customer_id, category, sentiment_label, sentiment_score,
            channel, created_at
        """
        if self.backend == "chromadb":
            return self._search_chromadb(query, top_k, filter_sentiment, filter_category)
        elif self.backend == "tfidf":
            return self._search_tfidf(query, top_k)
        else:
            # Substring fallback
            if self._fallback_df is not None:
                mask = self._fallback_df["feedback_text"].str.contains(
                    query, case=False, na=False
                )
                return self._fallback_df[mask].head(top_k).to_dict(orient="records")
            return []

    def _search_chromadb(
        self,
        query: str,
        top_k: int,
        filter_sentiment: Optional[str],
        filter_category: Optional[str],
    ) -> list[dict]:
        self._load_model()
        if self.collection is None:
            self._init_chroma()
        if self.collection.count() == 0:
            raise Exception("ChromaDB index is empty. Run pipeline first.")

        query_embedding = self.model.encode([query], convert_to_numpy=True).tolist()

        where_filter = {}
        if filter_sentiment:
            where_filter["sentiment_label"] = {"$eq": filter_sentiment}
        if filter_category:
            where_filter["category"] = {"$eq": filter_category}

        kwargs = dict(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        if where_filter:
            kwargs["where"] = where_filter

        results = self.collection.query(**kwargs)

        output = []
        docs      = results["documents"][0]
        metas     = results["metadatas"][0]
        distances = results["distances"][0]
        ids       = results["ids"][0]

        for doc, meta, dist, fid in zip(docs, metas, distances, ids):
            similarity = round(1 - dist, 4)   # cosine distance → similarity
            output.append({
                "feedback_id":     fid,
                "feedback_text":   doc,
                "similarity_score": similarity,
                **{k: v for k, v in meta.items()},
            })

        # seen_texts = {}
        # for item in output:
        #     text = item["feedback_text"]
        #     if text not in seen_texts or item["similarity_score"] > seen_texts[text]["similarity_score"]:
        #         seen_texts[text] = item
        # return list(seen_texts.values())[:top_k]
    # Return all results up to top_k (no deduplication - show all matches)
        return output[:top_k]

    def _search_tfidf(self, query: str, top_k: int) -> list[dict]:
        from sklearn.metrics.pairwise import cosine_similarity
        query_vec = self._fallback_tfidf.transform([query])
        scores    = cosine_similarity(query_vec, self._fallback_matrix).flatten()
        top_idx   = scores.argsort()[::-1][:top_k]

        results = []
        for idx in top_idx:
            if scores[idx] == 0:
                break
            row = self._fallback_df.iloc[idx].to_dict()
            row["similarity_score"] = round(float(scores[idx]), 4)
            results.append(row)
        return results

    # ── Persistence ───────────────────────────────────────────────────────────

    def is_index_built(self) -> bool:
        """Check if a persistent index exists on disk."""
        try:
            # First check: does chroma_db folder exist?
            if not Path(self.db_path).exists():
                logger.info(f"  ChromaDB path doesn't exist: {self.db_path}")
                return False
            
            # Check if chromadb is available
            try:
                import chromadb
            except ImportError:
                logger.info("  ChromaDB not installed, checking for feedback files...")
                # Fallback: check if parquet exists
                feedback_path = Path(__file__).parent / "artifacts" / "feedback_scored.parquet"
                return feedback_path.exists()
            
            # Try to connect to ChromaDB
            client = chromadb.PersistentClient(path=self.db_path)
            col = client.get_or_create_collection(_COLLECTION_NAME)
            doc_count = col.count()
            has_docs = doc_count > 0
            logger.info(f"  ChromaDB check: {doc_count} documents, index_built={has_docs}")
            return has_docs
            
        except Exception as e:
            logger.info(f"  ChromaDB check failed: {e}")
            # Check for parquet as fallback
            try:
                feedback_path = Path(__file__).parent / "artifacts" / "feedback_scored.parquet"
                exists = feedback_path.exists()
                logger.info(f"  Feedback parquet exists: {exists}")
                return exists
            except Exception as e2:
                logger.warning(f"  Fallback check failed: {e2}")
                return False

    def load_existing_index(self) -> "SemanticSearchEngine":
        """Load an already-built index from disk (ChromaDB, TF-IDF, or simple fallback)."""
        self.backend = self._init_backend()
        logger.info(f"Initializing search backend: {self.backend}")
        
        if self.backend == "chromadb":
            try:
                self._load_model()
                self._init_chroma()
                logger.info(f"Loaded ChromaDB index: {self.collection.count()} docs")
            except Exception as e:
                logger.warning(f"ChromaDB loading failed: {e}. Trying TF-IDF fallback...")
                self.backend = "tfidf"
        
        if self.backend == "tfidf":
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                feedback_path = Path(__file__).parent / "artifacts" / "feedback_scored.parquet"
                if feedback_path.exists():
                    self._fallback_df = pd.read_parquet(feedback_path)
                    logger.info(f"Loaded TF-IDF index from parquet: {len(self._fallback_df)} docs")
                    self._build_tfidf_from_df(self._fallback_df)
                else:
                    logger.warning("Feedback parquet not found for TF-IDF index")
            except Exception as e:
                logger.warning(f"TF-IDF loading failed: {e}")
                self.backend = "none"
        
        if self.backend == "none":
            # Load raw feedback for simple string matching
            feedback_path = Path(__file__).parent / "artifacts" / "feedback_scored.parquet"
            if feedback_path.exists():
                self._fallback_df = pd.read_parquet(feedback_path)
                logger.warning(f"Using basic fallback: {len(self._fallback_df)} docs (no ML features)")
        
        return self

    def _build_tfidf_from_df(self, df: pd.DataFrame) -> None:
        """Build TF-IDF index from existing dataframe."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            texts = df["feedback_text"].tolist()
            self._fallback_tfidf = TfidfVectorizer(max_features=100, stop_words="english")
            self._fallback_matrix = self._fallback_tfidf.fit_transform(texts)
            logger.info("TF-IDF vectorizer fitted successfully")
        except Exception as e:
            logger.warning(f"TF-IDF fitting failed: {e}")

    def get_index_stats(self) -> dict:
        if self.backend == "chromadb" and self.collection:
            return {"backend": "chromadb", "document_count": self.collection.count(),
                    "model": self.model_name, "db_path": self.db_path}
        elif self.backend == "tfidf" and self._fallback_df is not None:
            return {"backend": "tfidf", "document_count": len(self._fallback_df)}
        return {"backend": self.backend, "document_count": 0}


# ── Singleton ─────────────────────────────────────────────────────────────────

_search_engine: Optional[SemanticSearchEngine] = None


def get_search_engine() -> SemanticSearchEngine:
    global _search_engine

    if _search_engine is None:
        _search_engine = SemanticSearchEngine()
        try:
            _search_engine.load_existing_index()
            logger.info("Search index loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load search index: {e}")

    return _search_engine


if __name__ == "__main__":
    from feedback_generator import generate_feedback
    df = generate_feedback(n=100)

    engine = SemanticSearchEngine()
    engine.build_index(df)

    print("\nSearch: 'billing problem'")
    for r in engine.search("billing problem", top_k=5):
        print(f"  [{r['similarity_score']:.2f}] {r['feedback_text'][:80]}")

    print("\nSearch: 'slow internet speed'")
    for r in engine.search("slow internet speed", top_k=5):
        print(f"  [{r['similarity_score']:.2f}] {r['feedback_text'][:80]}")