"""
NLP API routes for SmartGrowth AI.

Add to app/main.py:
    from app.nlp_routes import router as nlp_router
    app.include_router(nlp_router, prefix="/nlp", tags=["NLP"])

Endpoints:
    GET  /nlp/search?q=billing+issue&top_k=10
    GET  /nlp/sentiment/timeline?freq=W
    GET  /nlp/sentiment/summary
    GET  /nlp/stats
    POST /nlp/rebuild
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

_pipeline = None

def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from ml_models.nlp.pipeline import get_nlp_pipeline
        _pipeline = get_nlp_pipeline()
    return _pipeline


# ── Response schemas ──────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    feedback_id:      str
    feedback_text:    str
    similarity_score: float
    sentiment_label:  Optional[str] = None
    category:         Optional[str] = None
    channel:          Optional[str] = None
    customer_id:      Optional[str] = None
    created_at:       Optional[str] = None


class SearchResponse(BaseModel):
    query:        str
    top_k:        int
    backend:      str
    results:      list[SearchResult]
    result_count: int


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/search", response_model=SearchResponse, summary="Semantic feedback search")
def semantic_search(
    q:                str = Query(..., min_length=2, description="Search query"),
    top_k:            int = Query(default=10, ge=1, le=50),
    filter_sentiment: Optional[str] = Query(default=None,
                          description="Filter: positive | negative | neutral"),
    filter_category:  Optional[str] = Query(default=None,
                          description="Filter by category"),
):
    """
    Search customer feedback by meaning, not just keywords.

    Example: searching 'billing problem' will also return
    'charged twice', 'wrong invoice', 'unexpected fee'.
    """
    pipeline = _get_pipeline()

    if pipeline.search_engine is None or not pipeline.search_engine.is_index_built():
        raise HTTPException(
            503,
            detail="Search index not built. Run: python -m ml_models.nlp.pipeline"
        )

    try:
        raw = pipeline.search(
            q, top_k=top_k,
            filter_sentiment=filter_sentiment,
            filter_category=filter_category,
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))

    results = []
    for r in raw:
        results.append(SearchResult(
            feedback_id=      str(r.get("feedback_id", "")),
            feedback_text=    str(r.get("feedback_text", "")),
            similarity_score= float(r.get("similarity_score", 0)),
            sentiment_label=  r.get("sentiment_label"),
            category=         r.get("category"),
            channel=          r.get("channel"),
            customer_id=      r.get("customer_id"),
            created_at=       str(r.get("created_at", "")) if r.get("created_at") else None,
        ))

    backend = pipeline.search_engine.backend if pipeline.search_engine else "unknown"
    return SearchResponse(query=q, top_k=top_k, backend=backend,
                          results=results, result_count=len(results))


@router.get("/sentiment/timeline", summary="Sentiment over time")
def get_sentiment_timeline(
    freq: str = Query(default="W", description="Aggregation: D=daily, W=weekly, ME=monthly"),
):
    """
    Returns aggregated sentiment scores over time.
    Used for the sentiment trend chart in the dashboard.
    """
    pipeline = _get_pipeline()
    df = pipeline.get_timeline(freq=freq)

    if df.empty:
        raise HTTPException(404, detail="Timeline not available. Run pipeline first.")

    # Convert period objects to strings for JSON serialization
    records = []
    for _, row in df.iterrows():
        records.append({
            "period":        str(row.get("period_str", row.get("period", ""))),
            "positive_pct":  round(float(row.get("positive_pct", 0)), 1),
            "negative_pct":  round(float(row.get("negative_pct", 0)), 1),
            "neutral_pct":   round(float(row.get("neutral_pct", 0)), 1),
            "net_sentiment": round(float(row.get("net_sentiment", 0)), 1),
            "total_count":   int(row.get("total_count", 0)),
            "trend":         round(float(row.get("trend", 0)), 1),
        })

    from ml_models.nlp.sentiment_analyzer import SentimentAnalyzer
    trend = SentimentAnalyzer.detect_trend(df)

    return {
        "freq":      freq,
        "periods":   len(records),
        "timeline":  records,
        "trend":     trend,
    }


@router.get("/sentiment/summary", summary="Sentiment distribution summary")
def get_sentiment_summary():
    """
    Overall sentiment breakdown, by category and by channel.
    Used for the pie/bar charts in the NLP dashboard tab.
    """
    pipeline = _get_pipeline()
    df = pipeline.get_feedback_df()

    if df.empty:
        raise HTTPException(404, detail="No feedback data available.")

    # Overall distribution
    overall = {}
    if "sentiment_label" in df.columns:
        dist = df["sentiment_label"].value_counts(normalize=True).mul(100).round(1)
        overall = dist.to_dict()

    # By category
    by_category = {}
    if "category" in df.columns and "sentiment_label" in df.columns:
        for cat in df["category"].unique():
            sub = df[df["category"] == cat]["sentiment_label"].value_counts(normalize=True)
            by_category[str(cat)] = {k: round(v * 100, 1) for k, v in sub.items()}

    # By channel
    by_channel = {}
    if "channel" in df.columns and "sentiment_label" in df.columns:
        for ch in df["channel"].unique():
            sub = df[df["channel"] == ch]["sentiment_label"].value_counts(normalize=True)
            by_channel[str(ch)] = {k: round(v * 100, 1) for k, v in sub.items()}

    # Negative rate over time (last 30 days vs prior 30)
    recent_negative_pct = None
    if "created_at" in df.columns and "sentiment_label" in df.columns:
        df2 = df.copy()
        df2["created_at"] = pd.to_datetime(df2["created_at"], errors="coerce")
        cutoff = df2["created_at"].max() - pd.Timedelta(days=30)
        recent = df2[df2["created_at"] >= cutoff]
        if len(recent) > 0:
            recent_negative_pct = round(
                (recent["sentiment_label"] == "negative").mean() * 100, 1
            )

    return {
        "total_feedback":        len(df),
        "overall":               overall,
        "by_category":           by_category,
        "by_channel":            by_channel,
        "recent_negative_pct":   recent_negative_pct,
    }


@router.get("/stats", summary="NLP pipeline stats")
def get_nlp_stats():
    """Returns pipeline metadata: index size, backend, model used."""
    pipeline = _get_pipeline()
    stats = pipeline.get_stats()
    if not stats:
        raise HTTPException(404, detail="Stats not available. Run pipeline first.")
    return stats


@router.post("/rebuild", summary="Rebuild NLP index (async)")
def rebuild_nlp(background_tasks: BackgroundTasks):
    """Triggers a full NLP pipeline rebuild in the background."""
    def _job():
        global _pipeline
        from ml_models.nlp.pipeline import NLPPipeline
        logger.info("NLP pipeline rebuild started...")
        p = NLPPipeline()
        p.run()
        _pipeline = p
        logger.info("NLP pipeline rebuild complete.")

    background_tasks.add_task(_job)
    return {"status": "rebuild_started",
            "message": "Check /nlp/stats in ~1 minute for results."}


# Needed for the sentinel check in get_sentiment_summary
try:
    import pandas as pd
except ImportError:
    pass