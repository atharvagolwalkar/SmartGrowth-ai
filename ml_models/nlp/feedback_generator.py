"""
Synthetic customer feedback generator for SmartGrowth AI NLP module.

Generates UNIQUE feedback by combining:
  - Template frames with {slot} placeholders
  - Random slot values (amounts, durations, names, products)
  - Light paraphrasing variants per template

Result: every record is textually distinct — no duplicates even at n=1000.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import numpy as np

# ── Slot value pools ──────────────────────────────────────────────────────────

_AMOUNTS      = ["₹200", "₹450", "₹850", "₹1,200", "$15", "$28", "$42", "$67", "$120"]
_DURATIONS    = ["2 days", "3 days", "a week", "10 days", "two weeks", "48 hours", "5 days"]
_PLAN_NAMES   = ["Basic", "Standard", "Premium", "Fiber Pro", "Business", "Unlimited"]
_WAIT_TIMES   = ["20 minutes", "45 minutes", "an hour", "90 minutes", "over an hour"]
_TIMES_OF_DAY = ["evenings", "peak hours", "nights", "weekends", "mornings"]
_SPEEDS       = ["5 Mbps", "8 Mbps", "12 Mbps", "3 Mbps", "15 Mbps"]
_PAID_SPEEDS  = ["100 Mbps", "200 Mbps", "50 Mbps", "500 Mbps", "1 Gbps"]
_AGENTS       = ["the agent", "the representative", "your team", "support staff", "the technician"]
_MONTHS       = ["January", "February", "March", "last month", "this month", "April", "October"]
_COMPETITORS  = ["Airtel", "Jio", "ACT", "BSNL", "the competitor", "another provider"]
_DEVICES      = ["laptop", "phone", "smart TV", "desktop", "all devices", "gaming console"]

# ── Template frames ───────────────────────────────────────────────────────────

_BILLING_TEMPLATES = [
    "I was charged {amount} twice this {month} and no one has helped me fix it yet.",
    "My bill went up by {amount} without any prior notice or explanation from your team.",
    "The invoice for {month} shows the {plan} plan but I never signed up for that.",
    "Auto-renewal happened even after I clearly requested cancellation {duration} ago.",
    "There are charges on my statement I cannot identify — please explain {amount}.",
    "The pricing on your website says {amount} but my bill shows something different.",
    "A refund of {amount} was promised {duration} ago and still hasn't reached my account.",
    "Hidden fees are making my monthly cost {amount} higher than what was advertised.",
    "The {plan} plan discount was applied incorrectly — I'm paying full price.",
    "Your payment portal keeps timing out and now I have a late fee of {amount}.",
    "I've been overcharged by {amount} for three consecutive months now.",
    "Billing support told me {amount} would be reversed within {duration} — still waiting.",
    "My {plan} plan was upgraded without consent and I'm now paying {amount} more.",
    "The GST charges on my bill don't match what was disclosed at signup.",
    "I cancelled in {month} but got charged again — please process the {amount} refund.",
    "Why am I being billed for equipment rental? I own my own modem.",
    "The loyalty discount I was promised is not showing on my {month} statement.",
    "I switched to {plan} plan but I'm still being billed at the old higher rate.",
]

_NETWORK_TEMPLATES = [
    "My internet drops every {time_of_day} and becomes completely unusable for {duration}.",
    "Speed tests show {slow_speed} when I'm paying for the {paid_speed} plan.",
    "Connection has been unstable for {duration} — this is affecting my work from home.",
    "Fiber installation was scheduled for {month} but the technician never showed up.",
    "Wi-Fi signal doesn't reach half my apartment despite being on the {plan} plan.",
    "There was a service outage in my area for over {duration} with zero updates.",
    "Constant packet loss makes video calls on my {device} impossible.",
    "My modem reboots itself multiple times every day — started {duration} ago.",
    "Upload is fine but download has been terrible since the last maintenance update.",
    "Cannot connect my {device} during {time_of_day} — happens every single day.",
    "The {plan} plan promises {paid_speed} but I'm consistently getting {slow_speed}.",
    "Signal drops every time it rains — this has been happening for {duration}.",
    "Streaming on my {device} keeps buffering since the network upgrade last {month}.",
    "Latency spikes to 400ms during {time_of_day} making gaming unplayable.",
    "The outage on {month} lasted {duration} and I received no compensation.",
    "My {device} keeps getting IP conflicts — your DHCP seems broken.",
    "Speeds drop to {slow_speed} every evening despite paying for {paid_speed}.",
]

_SUPPORT_NEGATIVE_TEMPLATES = [
    "Waited {wait} on hold and then the call dropped — completely unacceptable.",
    "I was transferred {count} times and had to repeat my entire issue every time.",
    "{agent} was dismissive and didn't even try to resolve my complaint.",
    "Promised a callback within {duration} — never received one.",
    "Chat support closed my ticket without resolving the billing issue.",
    "The technician arrived {duration} late and left without fixing anything.",
    "Nobody can give me a straight answer about my account status since {month}.",
    "This is the third time calling about the same problem — still no resolution.",
    "{agent} said they'd escalate but I've heard nothing since {month}.",
    "The automated system makes it impossible to reach a real person.",
    "I submitted a complaint {duration} ago and it's still showing as pending.",
    "Your chat bot is useless — it just loops me back to the same FAQ page.",
    "{agent} put me on hold for {wait} then disconnected without warning.",
    "I've sent {count} emails to support with no meaningful response.",
    "The resolution window keeps getting extended — now it's been {duration}.",
    "Support promised a technician visit but nobody showed up in {month}.",
    "I had to explain the same issue to {count} different agents in one day.",
    "Your support is only available 9-5 but the outages happen at night.",
]

_SUPPORT_POSITIVE_TEMPLATES = [
    "{agent} resolved my billing issue in under 10 minutes — very impressed.",
    "The technician arrived right on time and fixed everything within {duration}.",
    "Chat support was responsive and solved my {plan} plan issue immediately.",
    "Very impressed with how quickly the {month} outage was restored.",
    "{agent} went above and beyond — genuinely the best support experience I've had.",
    "Upgrading to the {plan} plan was seamless — smooth process start to finish.",
    "The new app makes managing my account on my {device} so much easier.",
    "Refund of {amount} was processed faster than expected — very happy.",
    "{agent} was patient, clear, and resolved everything in one call.",
    "Installation was quick and the technician explained everything thoroughly.",
    "I was skeptical after past issues but {agent} completely turned it around.",
    "Response time on chat was under {wait} — that's how support should work.",
    "The {plan} plan switch was handled perfectly, no billing errors at all.",
    "Proactive outage notification in {month} was a great improvement.",
    "{agent} followed up the next day to confirm everything was working.",
    "Self-service portal worked perfectly — cancelled an add-on instantly.",
    "Speed improvement after the upgrade to {plan} plan is very noticeable.",
    "Support team resolved my {device} connectivity issue remotely — impressive.",
]

_PRODUCT_POSITIVE_TEMPLATES = [
    "Speed is consistently {paid_speed} even during {time_of_day} — very satisfied.",
    "Uptime has been excellent this {month} — barely any interruptions.",
    "The new features in the app are genuinely useful for managing my {device}.",
    "Best value for money on the {plan} plan compared to {competitor}.",
    "Happy with the service overall — would recommend to friends and family.",
    "Streaming quality on my {device} is perfect — no buffering at all.",
    "Setup was straightforward and the {plan} plan works well with all my devices.",
    "Price of the {plan} plan is fair and speed consistently matches the promise.",
    "Stable {paid_speed} connection is exactly what I needed for work from home.",
    "Switched from {competitor} and the difference in reliability is remarkable.",
    "No outages in {month} — that's what I'm paying the {plan} plan price for.",
    "The router provided with {plan} plan covers my entire flat without issues.",
    "Speeds have actually improved since last {month} — appreciate the upgrade.",
    "Finally a provider that delivers {paid_speed} during {time_of_day} too.",
    "My {device} hasn't dropped connection once since I switched to {plan} plan.",
    "Data usage dashboard in the app is clear and accurate — great feature.",
    "Consistent low latency on the {plan} plan makes gaming on my {device} great.",
]

_CANCELLATION_TEMPLATES = [
    "If the speed stays at {slow_speed} I'm switching to {competitor} next month.",
    "Seriously considering cancelling after {duration} of unresolved issues.",
    "Already comparing {competitor} plans because of this ongoing problem.",
    "This is the last straw — calling to cancel my {plan} plan tomorrow.",
    "My contract ends in {month} and I won't be renewing at this service level.",
    "Friends switched to {competitor} and I'm seriously starting to agree.",
    "I filed a complaint in {month} and got no response — looking at my legal options.",
    "Three months of slow speeds and ignored tickets — I'm done.",
    "Telling everyone I know to avoid this provider and try {competitor}.",
    "One more outage like {month} and I'm cancelling the {plan} plan immediately.",
    "The {amount} price hike with zero service improvement has made my decision easy.",
    "I've been loyal for years but {duration} of bad service has ended that.",
    "Downgrading to {competitor} would be better than this {plan} plan.",
    "Asked to cancel {duration} ago — still being billed and no one responds.",
    "After {duration} of unresolved network issues my patience is completely gone.",
    "Your retention team offered nothing useful — cancellation request stands.",
    "I've documented {duration} of outages — sending this to the regulator.",
    "Moving to {competitor} next {month} unless this is fixed immediately.",
]

_CATEGORIES = {
    "billing":             (_BILLING_TEMPLATES,           -0.72),
    "network":             (_NETWORK_TEMPLATES,            -0.50),
    "support_negative":    (_SUPPORT_NEGATIVE_TEMPLATES,  -0.62),
    "support_positive":    (_SUPPORT_POSITIVE_TEMPLATES,   0.80),
    "product_positive":    (_PRODUCT_POSITIVE_TEMPLATES,   0.75),
    "cancellation_intent": (_CANCELLATION_TEMPLATES,      -0.85),
}

# ── Slot filler ───────────────────────────────────────────────────────────────

def _fill_slots(template: str, rng: random.Random) -> str:
    replacements = {
        "amount":      rng.choice(_AMOUNTS),
        "duration":    rng.choice(_DURATIONS),
        "plan":        rng.choice(_PLAN_NAMES),
        "wait":        rng.choice(_WAIT_TIMES),
        "time_of_day": rng.choice(_TIMES_OF_DAY),
        "slow_speed":  rng.choice(_SPEEDS),
        "paid_speed":  rng.choice(_PAID_SPEEDS),
        "agent":       rng.choice(_AGENTS),
        "month":       rng.choice(_MONTHS),
        "competitor":  rng.choice(_COMPETITORS),
        "device":      rng.choice(_DEVICES),
        "count":       str(rng.randint(2, 6)),
    }
    result = template
    for key, val in replacements.items():
        result = result.replace(f"{{{key}}}", val)
    return result


def _sentiment_label(score: float) -> str:
    if score > 0.2:
        return "positive"
    elif score < -0.2:
        return "negative"
    return "neutral"


# ── Main generator ────────────────────────────────────────────────────────────

def generate_feedback(
    n: int = 500,
    customer_ids: Optional[list] = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate n unique synthetic feedback records.

    Every record is textually distinct — templates are filled with
    randomized slot values so no two sentences are identical.
    """
    rng    = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    if customer_ids is None:
        customer_ids = [f"CUST-{i:04d}" for i in range(1, 201)]

    categories      = list(_CATEGORIES.keys())
    weights         = [0.15, 0.14, 0.14, 0.22, 0.22, 0.13]
    channels        = ["email", "chat", "phone", "app_review", "social"]
    channel_weights = [0.25, 0.30, 0.20, 0.15, 0.10]

    start_date   = datetime(2023, 1, 1)
    end_date     = datetime(2024, 12, 31)
    date_range   = (end_date - start_date).days

    rows       = []
    seen_texts = set()
    attempts   = 0
    max_attempts = n * 10

    while len(rows) < n and attempts < max_attempts:
        attempts += 1

        cat = rng.choices(categories, weights=weights, k=1)[0]
        templates, base_score = _CATEGORIES[cat]

        text = _fill_slots(rng.choice(templates), rng)

        if text in seen_texts:
            continue
        seen_texts.add(text)

        score = float(np.clip(base_score + np_rng.normal(0, 0.06), -1, 1))
        label = _sentiment_label(score)

        days_offset = rng.randint(0, date_range)
        created_at  = start_date + timedelta(
            days=days_offset,
            hours=rng.randint(8, 22),
            minutes=rng.randint(0, 59),
        )

        rows.append({
            "feedback_id":     f"FB-{len(rows)+1:05d}",
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
    df = generate_feedback(n=500)
    print(f"Generated:    {len(df)} records")
    print(f"Unique texts: {df['feedback_text'].nunique()}")
    print(f"\nSentiment:\n{df['sentiment_label'].value_counts(normalize=True).mul(100).round(1)}")
    print(f"\nCategories:\n{df['category'].value_counts()}")
    print(f"\nSample:")
    for _, row in df.head(6).iterrows():
        print(f"  [{row['sentiment_label']:8s}] {row['feedback_text']}")