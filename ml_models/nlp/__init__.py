"""
SmartGrowth AI — NLP Module
==============================

Two core capabilities:
  1. Semantic Search  — find feedback by meaning using sentence-transformers + ChromaDB
  2. Sentiment Timeline — track customer satisfaction trends over time

Backends (auto-selected based on what's installed):
  sentence-transformers + chromadb  →  best (semantic embeddings)
  sklearn TF-IDF                    →  fallback (keyword-based)
  built-in lexicon                  →  last resort (zero deps)

Public API:
    from ml_models.nlp import NLPPipeline, get_nlp_pipeline

    # Build index + run sentiment (one-time)
    pipeline = NLPPipeline()
    pipeline.run()

    # Search
    results = pipeline.search("billing complaint", top_k=10)

    # Timeline
    df = pipeline.get_timeline(freq="W")
"""

from .feedback_generator import generate_feedback
from .semantic_search import SemanticSearchEngine, get_search_engine
from .sentiment_analyzer import SentimentAnalyzer, get_sentiment_analyzer
from .pipeline import NLPPipeline, get_nlp_pipeline

__all__ = [
    "generate_feedback",
    "SemanticSearchEngine",
    "get_search_engine",
    "SentimentAnalyzer",
    "get_sentiment_analyzer",
    "NLPPipeline",
    "get_nlp_pipeline",
]

__version__ = "1.0.0"