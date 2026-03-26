"""
Sentiment Analyzer — SmartGrowth AI NLP Module

Uses cardiffnlp/twitter-roberta-base-sentiment (pretrained transformer,
zero fine-tuning needed) to score customer feedback.

Three-class output: positive / neutral / negative with confidence scores.

Also provides:
  - Sentiment timeline aggregation (daily/weekly/monthly)
  - Segment-level sentiment (by contract type, tenure band, risk level)
  - Churn correlation: do high-risk customers leave more negative feedback?
  - Trend detection: is sentiment improving or worsening?

Falls back to VADER (rule-based) if transformers not installed,
and to a simple lexicon if VADER is also missing.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_HF_MODEL    = "cardiffnlp/twitter-roberta-base-sentiment"
_VADER_MODEL = "vader"


class SentimentAnalyzer:
    """
    Sentiment analysis with three backends (auto-selected):
      1. RoBERTa (cardiffnlp) — best accuracy, needs transformers + torch
      2. VADER              — fast, rule-based, no GPU needed
      3. Lexicon fallback   — zero deps, least accurate
    """

    def __init__(self, model: str = "auto"):
        self.model_name = model
        self.pipeline   = None
        self.vader      = None
        self.backend    = "none"
        self._label_map = {"LABEL_0": "negative", "LABEL_1": "neutral", "LABEL_2": "positive",
                           "negative": "negative", "neutral": "neutral", "positive": "positive",
                           "pos": "positive", "neg": "negative", "neu": "neutral"}

    # ── Backend selection ─────────────────────────────────────────────────────

    def _detect_backend(self) -> str:
        if self.model_name != "auto":
            return self.model_name
        try:
            import transformers  # noqa
            import torch          # noqa
            return "roberta"
        except ImportError:
            pass
        try:
            import nltk           # noqa
            return "vader"
        except ImportError:
            pass
        return "lexicon"

    def load(self) -> "SentimentAnalyzer":
        """Load the best available model."""
        self.backend = self._detect_backend()
        logger.info(f"Sentiment backend: {self.backend}")

        if self.backend == "roberta":
            self._load_roberta()
        elif self.backend == "vader":
            self._load_vader()
        # lexicon needs no loading

        return self

    def _load_roberta(self) -> None:
        from transformers import pipeline as hf_pipeline
        logger.info(f"Loading {_HF_MODEL} (first run downloads ~500MB)...")
        self.pipeline = hf_pipeline(
            "sentiment-analysis",
            model=_HF_MODEL,
            tokenizer=_HF_MODEL,
            max_length=128,
            truncation=True,
            device=-1,   # CPU; change to 0 for GPU
        )
        logger.info("RoBERTa sentiment model loaded.")

    def _load_vader(self) -> None:
        import nltk
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        self.vader = SentimentIntensityAnalyzer()
        logger.info("VADER sentiment analyzer loaded.")

    # ── Scoring ───────────────────────────────────────────────────────────────

    def score(self, text: str) -> dict:
        """
        Score a single text.

        Returns:
            {"label": "positive"|"neutral"|"negative",
             "score": float 0-1,
             "scores": {"positive": f, "neutral": f, "negative": f}}
        """
        if not self.backend or self.backend == "none":
            self.load()

        if self.backend == "roberta":
            return self._score_roberta(text)
        elif self.backend == "vader":
            return self._score_vader(text)
        else:
            return self._score_lexicon(text)

    def _score_roberta(self, text: str) -> dict:
        result = self.pipeline(text[:512])[0]
        label  = self._label_map.get(result["label"], "neutral")
        conf   = float(result["score"])
        # Reconstruct approximate full distribution
        if label == "positive":
            scores = {"positive": conf, "neutral": (1-conf)*0.4, "negative": (1-conf)*0.6}
        elif label == "negative":
            scores = {"negative": conf, "neutral": (1-conf)*0.4, "positive": (1-conf)*0.6}
        else:
            scores = {"neutral": conf, "positive": (1-conf)*0.5, "negative": (1-conf)*0.5}
        return {"label": label, "score": conf, "scores": scores}

    def _score_vader(self, text: str) -> dict:
        vs = self.vader.polarity_scores(text)
        compound = vs["compound"]
        if compound >= 0.05:
            label = "positive"
            score = (compound + 1) / 2
        elif compound <= -0.05:
            label = "negative"
            score = (-compound + 1) / 2
        else:
            label = "neutral"
            score = 0.5
        scores = {"positive": vs["pos"], "neutral": vs["neu"], "negative": vs["neg"]}
        return {"label": label, "score": round(score, 4), "scores": scores}

    def _score_lexicon(self, text: str) -> dict:
        """Minimal positive/negative word count fallback."""
        pos_words = {"good","great","excellent","happy","satisfied","fast","easy",
                     "resolved","helpful","professional","quick","smooth","best"}
        neg_words = {"bad","terrible","awful","slow","broken","angry","frustrated",
                     "issue","problem","failed","wrong","never","worst","useless",
                     "cancelled","charged","overcharged","waiting","rude","dismissed"}
        tokens = set(text.lower().split())
        pos = len(tokens & pos_words)
        neg = len(tokens & neg_words)
        if pos > neg:
            return {"label": "positive", "score": 0.7,
                    "scores": {"positive": 0.7, "neutral": 0.2, "negative": 0.1}}
        elif neg > pos:
            return {"label": "negative", "score": 0.7,
                    "scores": {"negative": 0.7, "neutral": 0.2, "positive": 0.1}}
        return {"label": "neutral", "score": 0.5,
                "scores": {"neutral": 0.6, "positive": 0.2, "negative": 0.2}}

    # ── Batch scoring ─────────────────────────────────────────────────────────

    def score_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str = "feedback_text",
        batch_size: int = 32,
    ) -> pd.DataFrame:
        """
        Score all rows in a DataFrame. Adds columns:
            sentiment_label, sentiment_score, sentiment_positive,
            sentiment_neutral, sentiment_negative
        """
        if not self.backend or self.backend == "none":
            self.load()

        results = []
        texts = df[text_col].tolist()

        if self.backend == "roberta" and self.pipeline:
            # Batch inference is much faster with transformers
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]
                batch = [t[:512] for t in batch]
                raw   = self.pipeline(batch)
                for r in raw:
                    label = self._label_map.get(r["label"], "neutral")
                    conf  = float(r["score"])
                    results.append({"sentiment_label": label, "sentiment_score": conf})
        else:
            for text in texts:
                r = self.score(str(text))
                results.append({"sentiment_label": r["label"], "sentiment_score": r["score"]})

        scored = pd.DataFrame(results)
        out = df.copy()
        out["sentiment_label"] = scored["sentiment_label"].values
        out["sentiment_score"] = scored["sentiment_score"].values
        return out

    # ── Timeline aggregation ──────────────────────────────────────────────────

    @staticmethod
    def build_timeline(
        df: pd.DataFrame,
        freq: str = "W",            # "D" daily, "W" weekly, "ME" monthly
        date_col: str = "created_at",
        label_col: str = "sentiment_label",
        score_col: str = "sentiment_score",
    ) -> pd.DataFrame:
        """
        Aggregate sentiment over time.

        Returns DataFrame with columns:
            period, positive_pct, negative_pct, neutral_pct,
            avg_score, total_count, net_sentiment
        """
        work = df.copy()
        work[date_col] = pd.to_datetime(work[date_col])
        work["period"] = work[date_col].dt.to_period(freq)

        agg = work.groupby("period").apply(lambda g: pd.Series({
            "positive_pct": (g[label_col] == "positive").mean() * 100,
            "negative_pct": (g[label_col] == "negative").mean() * 100,
            "neutral_pct":  (g[label_col] == "neutral").mean()  * 100,
            "avg_score":     g[score_col].mean() if score_col in g.columns else 0.5,
            "total_count":   len(g),
        }), include_groups=False).reset_index()

        agg["net_sentiment"] = agg["positive_pct"] - agg["negative_pct"]
        agg["period_str"]    = agg["period"].astype(str)

        # Rolling 3-period trend
        agg["trend"] = agg["net_sentiment"].rolling(3, min_periods=1).mean()
        return agg

    @staticmethod
    def sentiment_by_segment(
        df: pd.DataFrame,
        segment_col: str,
        label_col: str = "sentiment_label",
    ) -> pd.DataFrame:
        """
        Compute sentiment breakdown per segment value.
        E.g. segment_col = "category" or "channel"
        """
        if segment_col not in df.columns:
            return pd.DataFrame()

        result = df.groupby(segment_col)[label_col].value_counts(normalize=True)\
                   .mul(100).round(1).reset_index()
        result.columns = [segment_col, "sentiment", "percentage"]
        return result

    @staticmethod
    def detect_trend(timeline: pd.DataFrame, window: int = 4) -> dict:
        """
        Detect whether sentiment is improving, worsening, or stable.

        Returns dict with direction, magnitude, and summary string.
        """
        if len(timeline) < 2:
            return {"direction": "stable", "magnitude": 0.0, "summary": "Insufficient data"}

        recent = timeline["net_sentiment"].tail(window)
        older  = timeline["net_sentiment"].head(max(1, len(timeline) - window))

        recent_avg = recent.mean()
        older_avg  = older.mean()
        delta      = recent_avg - older_avg

        if delta > 5:
            direction = "improving"
            emoji = "↑"
        elif delta < -5:
            direction = "worsening"
            emoji = "↓"
        else:
            direction = "stable"
            emoji = "→"

        return {
            "direction":   direction,
            "magnitude":   round(abs(delta), 1),
            "recent_avg":  round(recent_avg, 1),
            "older_avg":   round(older_avg, 1),
            "summary":     f"{emoji} Sentiment {direction} ({delta:+.1f}pp vs prior period)",
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
        _analyzer.load()
    return _analyzer


if __name__ == "__main__":
    from feedback_generator import generate_feedback

    df = generate_feedback(n=50)
    analyzer = SentimentAnalyzer()
    analyzer.load()

    # Score sample
    print("Sample scores:")
    for text in df["feedback_text"].head(5):
        r = analyzer.score(text)
        print(f"  [{r['label']:8s} {r['score']:.2f}]  {text[:70]}")

    # Timeline
    df_scored = analyzer.score_dataframe(df)
    timeline  = SentimentAnalyzer.build_timeline(df_scored, freq="ME")
    print("\nMonthly sentiment timeline:")
    print(timeline[["period_str","positive_pct","negative_pct","net_sentiment","total_count"]]
          .tail(6).to_string(index=False))

    trend = SentimentAnalyzer.detect_trend(timeline)
    print(f"\nTrend: {trend['summary']}")