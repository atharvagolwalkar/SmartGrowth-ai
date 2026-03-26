"""
Synthetic customer feedback generator for SmartGrowth AI NLP module.

Generates realistic support tickets and reviews covering:
- Billing complaints
- Network/service issues
- Customer support experiences
- Product satisfaction
- Cancellation intent

Used to seed the customer_feedback table if real data is sparse.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import numpy as np

# ── Template pools ────────────────────────────────────────────────────────────

_BILLING_COMPLAINTS = [
    "I was charged twice this month and no one is helping me fix it.",
    "My bill went up by $20 without any notice or explanation.",
    "The invoice shows services I never signed up for.",
    "Auto-renewal happened even after I tried to cancel.",
    "I can't understand the charges on my statement at all.",
    "The pricing on the website doesn't match what I'm being billed.",
    "Refund promised 2 weeks ago still hasn't arrived in my account.",
    "Hidden fees are making my monthly cost way higher than advertised.",
    "Discount applied incorrectly — I'm paying full price on a promo plan.",
    "Payment portal keeps failing and now I have a late fee.",
]

_NETWORK_ISSUES = [
    "Internet drops every night around 8pm, completely unusable.",
    "Speed test shows 5 Mbps when I'm paying for 100 Mbps.",
    "Connection has been unstable for three days now.",
    "Fiber line was supposed to be installed but technician never showed.",
    "Wifi signal is weak in half my apartment despite full plan.",
    "Service outage in my area for over 12 hours with no updates.",
    "Constant packet loss makes video calls impossible to use.",
    "Modem keeps rebooting itself multiple times per day.",
    "Upload speed is fine but download is terrible since last update.",
    "Cannot connect any devices during peak hours.",
]

_SUPPORT_NEGATIVE = [
    "Waited 45 minutes on hold and then the call dropped.",
    "Was transferred four times and had to repeat my issue every time.",
    "Support agent was rude and dismissive about my complaint.",
    "Promised callback within 24 hours — never received it.",
    "Chat support closed my ticket without resolving the issue.",
    "Technician arrived late and left without fixing the problem.",
    "No one can give me a straight answer about my account status.",
    "Third time calling about the same issue and still no resolution.",
    "Support said they'd escalate but I've heard nothing since.",
    "Automated system makes it impossible to reach a real person.",
]

_SUPPORT_POSITIVE = [
    "Agent resolved my billing issue quickly and professionally.",
    "Technician arrived on time and fixed everything in under an hour.",
    "Chat support was responsive and solved my problem right away.",
    "Very impressed with how quickly the outage was resolved.",
    "Customer service went above and beyond to help me today.",
    "Had a great experience upgrading my plan — smooth process.",
    "The new app makes managing my account so much easier.",
    "Refund processed faster than expected, very happy.",
    "Support agent was patient and explained everything clearly.",
    "Installation was quick and the technician was very professional.",
]

_PRODUCT_POSITIVE = [
    "Speed is consistently fast even during peak hours.",
    "Uptime has been excellent, barely any interruptions this year.",
    "The new features in the app are really useful.",
    "Best value for money compared to other providers I've tried.",
    "Happy with the service overall, would recommend to others.",
    "Streaming quality is perfect with this plan.",
    "Easy to set up and works well with all my devices.",
    "Price is fair and the speed matches what was promised.",
    "Stable connection is all I needed and this delivers.",
    "Switched from a competitor and the difference is noticeable.",
]

_CANCELLATION_INTENT = [
    "If this keeps up I'm switching to a competitor next month.",
    "Seriously considering cancelling after this experience.",
    "Already looking at other providers because of this ongoing issue.",
    "This is the last straw — I'll be calling to cancel tomorrow.",
    "My contract ends soon and I won't be renewing at this rate.",
    "Friends recommended switching and I'm starting to agree.",
    "Filed a complaint with the regulator and looking at my options.",
    "Three months of poor service, I'm done with this company.",
    "Telling everyone I know to avoid this provider.",
    "One more outage and I'm cancelling immediately.",
]

_CATEGORIES = {
    "billing":            (_BILLING_COMPLAINTS,  -0.7),
    "network":            (_NETWORK_ISSUES,       -0.5),
    "support_negative":   (_SUPPORT_NEGATIVE,     -0.6),
    "support_positive":   (_SUPPORT_POSITIVE,      0.8),
    "product_positive":   (_PRODUCT_POSITIVE,      0.75),
    "cancellation_intent":(_CANCELLATION_INTENT,  -0.85),
}

# sentiment label from base score + noise
def _sentiment_label(score: float) -> str:
    if score > 0.2:
        return "positive"
    elif score < -0.2:
        return "negative"
    return "neutral"


def generate_feedback(
    n: int = 500,
    customer_ids: Optional[list] = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate n synthetic feedback records.

    Returns DataFrame with columns:
        feedback_id, customer_id, feedback_text, category,
        sentiment_score, sentiment_label, created_at, channel
    """
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    if customer_ids is None:
        customer_ids = [f"CUST-{i:04d}" for i in range(1, 201)]

    # Category weights — slightly skewed negative (realistic)
    categories = list(_CATEGORIES.keys())
    weights = [0.20, 0.18, 0.20, 0.15, 0.15, 0.12]

    channels = ["email", "chat", "phone", "app_review", "social"]
    channel_weights = [0.25, 0.30, 0.20, 0.15, 0.10]

    rows = []
    start_date = datetime(2023, 1, 1)
    end_date   = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days

    for i in range(n):
        cat = rng.choices(categories, weights=weights, k=1)[0]
        templates, base_score = _CATEGORIES[cat]
        text = rng.choice(templates)

        # Add slight variation with noise
        score = float(np.clip(base_score + np_rng.normal(0, 0.08), -1, 1))
        label = _sentiment_label(score)

        days_offset = rng.randint(0, date_range)
        created_at = start_date + timedelta(days=days_offset,
                                             hours=rng.randint(8, 22),
                                             minutes=rng.randint(0, 59))

        rows.append({
            "feedback_id":     f"FB-{i+1:05d}",
            "customer_id":     rng.choice(customer_ids),
            "feedback_text":   text,
            "category":        cat,
            "sentiment_score": round(score, 4),
            "sentiment_label": label,
            "created_at":      created_at,
            "channel":         rng.choices(channels, weights=channel_weights, k=1)[0],
        })

    df = pd.DataFrame(rows).sort_values("created_at").reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generate_feedback(n=200)
    print(df.head(10).to_string())
    print(f"\nShape: {df.shape}")
    print(f"\nCategory distribution:\n{df['category'].value_counts()}")
    print(f"\nSentiment distribution:\n{df['sentiment_label'].value_counts()}")