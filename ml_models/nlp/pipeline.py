"""
NLP Pipeline — SmartGrowth AI

Orchestrates the full NLP lifecycle:
  1. Load feedback from DB (or generate synthetic if empty)
  2. Score all feedback with sentiment analyzer
  3. Build semantic search index (ChromaDB / TF-IDF fallback)
  4. Save scored feedback + timeline to artifacts/
  5. Expose singleton getters for FastAPI

Run once to set up:
    python -m ml_models.nlp.pipeline

Then the FastAPI NLP routes auto-load on startup.
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Optional

import pandas as pd

from .feedback_generator import generate_feedback
from .semantic_search import SemanticSearchEngine, get_search_engine
from .sentiment_analyzer import SentimentAnalyzer, get_sentiment_analyzer

logger = logging.getLogger(__name__)

_ARTIFACT_DIR    = Path(__file__).parent / "artifacts"
_FEEDBACK_CACHE  = _ARTIFACT_DIR / "feedback_scored.parquet"
_TIMELINE_CACHE  = _ARTIFACT_DIR / "sentiment_timeline.parquet"
_STATS_FILE      = _ARTIFACT_DIR / "nlp_stats.json"


class NLPPipeline:
    """
    Full NLP pipeline: feedback loading → sentiment → search index.

    Quick start:
        pipeline = NLPPipeline()
        pipeline.run()

    Then use:
        pipeline.search("billing issue", top_k=10)
        pipeline.get_timeline(freq="W")
        pipeline.get_stats()
    """

    def __init__(self, artifact_dir: Optional[str] = None):
        self.artifact_dir = Path(artifact_dir) if artifact_dir else _ARTIFACT_DIR
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

        self.search_engine: Optional[SemanticSearchEngine] = None
        self.analyzer:      Optional[SentimentAnalyzer]    = None
        self.feedback_df:   Optional[pd.DataFrame]         = None
        self.timeline_df:   Optional[pd.DataFrame]         = None
        self.stats:         dict                           = {}

    # ── Full pipeline run ─────────────────────────────────────────────────────

    def run(self, db_engine=None, n_synthetic: int = 500) -> dict:
        """
        Run the full pipeline. Pass a SQLAlchemy engine to use real DB data,
        or leave None to generate synthetic feedback.
        """
        logger.info("=" * 55)
        logger.info("SmartGrowth AI — NLP Pipeline")
        logger.info("=" * 55)

        # 1. Load / generate feedback
        df = self._load_feedback(db_engine, n_synthetic)
        logger.info(f"Feedback loaded: {len(df)} records")

        # 2. Sentiment scoring
        logger.info("\n[1/2] Running sentiment analysis...")
        self.analyzer = SentimentAnalyzer()
        self.analyzer.load()

        # Only score rows that don't already have sentiment
        if "sentiment_label" not in df.columns or df["sentiment_label"].isna().any():
            df = self.analyzer.score_dataframe(df)
        else:
            logger.info("  Sentiment already present — skipping re-scoring.")

        self.feedback_df = df

        # 3. Timeline
        self.timeline_df = SentimentAnalyzer.build_timeline(df, freq="W")

        # 4. Semantic search index
        logger.info("\n[2/2] Building semantic search index...")
        self.search_engine = SemanticSearchEngine(
            db_path=str(self.artifact_dir / "chroma_db")
        )
        self.search_engine.build_index(df)

        # 5. Save artifacts
        self._save_artifacts()

        # 6. Stats
        self.stats = self._compute_stats(df)
        with open(_STATS_FILE, "w") as f:
            json.dump(self.stats, f, indent=2)

        logger.info("\nNLP Pipeline complete.")
        self._print_summary()
        return self.stats

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load_feedback(self, db_engine, n_synthetic: int) -> pd.DataFrame:
        """Try DB first, fall back to synthetic."""
        if db_engine is not None:
            try:
                from sqlalchemy import text
                df = pd.read_sql(
                    text("SELECT * FROM customer_feedback ORDER BY created_at"),
                    db_engine,
                )
                if len(df) >= 20:
                    logger.info(f"  Loaded {len(df)} rows from customer_feedback table.")
                    return df
                else:
                    logger.info(f"  Only {len(df)} rows in DB — supplementing with synthetic data.")
            except Exception as e:
                logger.warning(f"  DB load failed ({e}) — using synthetic data.")

        logger.info(f"  Generating {n_synthetic} synthetic feedback records...")
        return generate_feedback(n=n_synthetic)

    # ── Inference (used by FastAPI) ────────────────────────────────────────────

    def search(self, query: str, top_k: int = 10, **kwargs) -> list[dict]:
        if self.search_engine is None:
            self.load()
        return self.search_engine.search(query, top_k=top_k, **kwargs)

    def get_timeline(self, freq: str = "W") -> pd.DataFrame:
        if self.timeline_df is not None:
            return self.timeline_df
        # Try loading from cache
        cache = self.artifact_dir / "sentiment_timeline.parquet"
        if cache.exists():
            self.timeline_df = pd.read_parquet(cache)
            return self.timeline_df
        return pd.DataFrame()

    def get_feedback_df(self) -> pd.DataFrame:
        if self.feedback_df is not None:
            return self.feedback_df
        cache = self.artifact_dir / "feedback_scored.parquet"
        if cache.exists():
            self.feedback_df = pd.read_parquet(cache)
        return self.feedback_df or pd.DataFrame()

    def get_stats(self) -> dict:
        if self.stats:
            return self.stats
        if _STATS_FILE.exists():
            with open(_STATS_FILE) as f:
                self.stats = json.load(f)
        return self.stats

    # ── Load saved artifacts ──────────────────────────────────────────────────

    def load(self) -> "NLPPipeline":
        """Load all pipeline artifacts from disk."""
        logger.info("Loading NLP pipeline artifacts...")

        feedback_cache  = self.artifact_dir / "feedback_scored.parquet"
        timeline_cache  = self.artifact_dir / "sentiment_timeline.parquet"

        if feedback_cache.exists():
            self.feedback_df = pd.read_parquet(feedback_cache)
            logger.info(f"  Feedback loaded: {len(self.feedback_df)} rows")

        if timeline_cache.exists():
            self.timeline_df = pd.read_parquet(timeline_cache)
            logger.info(f"  Timeline loaded: {len(self.timeline_df)} periods")

        if _STATS_FILE.exists():
            with open(_STATS_FILE) as f:
                self.stats = json.load(f)

        # Search engine (loads index from chroma_db/ on disk)
        self.search_engine = SemanticSearchEngine(
            db_path=str(self.artifact_dir / "chroma_db")
        )
        if self.search_engine.is_index_built():
            self.search_engine.load_existing_index()
            logger.info(f"  Search index loaded: {self.search_engine.get_index_stats()}")
        else:
            logger.warning("  Search index not found — run pipeline.run() to build it.")

        self.analyzer = SentimentAnalyzer()
        self.analyzer.load()

        return self

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _save_artifacts(self) -> None:
        if self.feedback_df is not None:
            p = self.artifact_dir / "feedback_scored.parquet"
            self.feedback_df.to_parquet(p, index=False)
            logger.info(f"  Saved feedback → {p}")

        if self.timeline_df is not None:
            p = self.artifact_dir / "sentiment_timeline.parquet"
            self.timeline_df.to_parquet(p, index=False)
            logger.info(f"  Saved timeline → {p}")

    def _compute_stats(self, df: pd.DataFrame) -> dict:
        stats = {
            "total_feedback": len(df),
            "sentiment_distribution": {},
            "category_distribution": {},
            "channel_distribution": {},
            "avg_sentiment_score": 0.0,
            "index_stats": {},
        }

        if "sentiment_label" in df.columns:
            dist = df["sentiment_label"].value_counts(normalize=True).mul(100).round(1)
            stats["sentiment_distribution"] = dist.to_dict()

        if "category" in df.columns:
            cat = df["category"].value_counts().to_dict()
            stats["category_distribution"] = {str(k): int(v) for k, v in cat.items()}

        if "channel" in df.columns:
            ch = df["channel"].value_counts().to_dict()
            stats["channel_distribution"] = {str(k): int(v) for k, v in ch.items()}

        if "sentiment_score" in df.columns:
            stats["avg_sentiment_score"] = round(float(df["sentiment_score"].mean()), 4)

        if self.search_engine:
            stats["index_stats"] = self.search_engine.get_index_stats()

        if self.timeline_df is not None and len(self.timeline_df) > 1:
            trend = SentimentAnalyzer.detect_trend(self.timeline_df)
            stats["trend"] = trend

        return stats

    def _print_summary(self) -> None:
        s = self.stats
        print(f"\nTotal feedback:  {s.get('total_feedback', 0):,}")
        print(f"Sentiment dist:  {s.get('sentiment_distribution', {})}")
        print(f"Avg score:       {s.get('avg_sentiment_score', 0):.3f}")
        if "trend" in s:
            print(f"Trend:           {s['trend']['summary']}")
        print(f"Index:           {s.get('index_stats', {})}")


# ── Singleton ─────────────────────────────────────────────────────────────────

_nlp_pipeline: Optional[NLPPipeline] = None


def get_nlp_pipeline() -> NLPPipeline:
    global _nlp_pipeline
    if _nlp_pipeline is None:
        _nlp_pipeline = NLPPipeline()
        if _STATS_FILE.exists():
            _nlp_pipeline.load()
        else:
            logger.warning("NLP pipeline not built. Run: python -m ml_models.nlp.pipeline")
    return _nlp_pipeline


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    parser = argparse.ArgumentParser(description="SmartGrowth AI NLP Pipeline")
    parser.add_argument("--n-synthetic", type=int, default=500,
                        help="Number of synthetic feedback records to generate")
    parser.add_argument("--use-db",  action="store_true",
                        help="Load real feedback from database")
    args = parser.parse_args()

    db_engine = None
    if args.use_db:
        try:
            from sqlalchemy import create_engine
            import os
            db_path = os.environ.get("DATABASE_URL", "sqlite:///smartgrowth.db")
            db_engine = create_engine(db_path)
            logger.info(f"Connected to DB: {db_path}")
        except Exception as e:
            logger.warning(f"DB connection failed: {e} — using synthetic data")

    pipeline = NLPPipeline()
    stats = pipeline.run(db_engine=db_engine, n_synthetic=args.n_synthetic)

    # Demo search
    print("\n--- Demo search ---")
    for query in ["billing problem", "service outage", "great support"]:
        results = pipeline.search(query, top_k=3)
        print(f"\n'{query}':")
        for r in results:
            print(f"  [{r.get('similarity_score', 0):.2f}] {r['feedback_text'][:75]}")