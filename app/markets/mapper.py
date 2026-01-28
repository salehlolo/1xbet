from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable, List

from app.api.base import Market, Outcome

LOW_PRIORITY_KEYWORDS = (
    "نتيجة صحيحة",
    "الهدف التالي",
    "حتى الدقيقة",
    "أرقام زوجية",
)

TOTAL_KEYWORDS = ("مجموع",)
ASIAN_TOTAL_KEYWORDS = ("المجموع الآسيوي",)
ASIAN_HANDICAP_KEYWORDS = ("هاندكاب آسيوي",)
EURO_HANDICAP_KEYWORDS = ("هاندكاب أوروبي",)
BTTS_KEYWORDS = ("كلا الفريقين سيسجل",)
TEAM_TOTAL_KEYWORDS = (
    "المجموع الآسيوي الخاص للفريق 1",
    "المجموع الآسيوي الخاص للفريق 2",
)
TEAM_TOTAL_PATTERNS = (
    re.compile(r"مجموع\\s+1\\b"),
    re.compile(r"مجموع\\s+2\\b"),
)


def _extract_line(text: str) -> float | None:
    match = re.search(r"(-?\d+\.?\d*)", text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _map_side(outcome_name: str) -> str | None:
    if "أكثر" in outcome_name or "فوق" in outcome_name:
        return "over"
    if "أقل" in outcome_name or "تحت" in outcome_name:
        return "under"
    if outcome_name.strip() in ("نعم", "لا"):
        return "yes" if outcome_name.strip() == "نعم" else "no"
    if "تعادل" in outcome_name:
        return "draw"
    if "فريق 1" in outcome_name or "صاحب" in outcome_name:
        return "home"
    if "فريق 2" in outcome_name or "ضيف" in outcome_name:
        return "away"
    return None


def is_low_priority(name: str) -> bool:
    return any(keyword in name for keyword in LOW_PRIORITY_KEYWORDS)


def is_team_total(name: str) -> bool:
    if any(keyword in name for keyword in TEAM_TOTAL_KEYWORDS):
        return True
    return any(pattern.search(name) for pattern in TEAM_TOTAL_PATTERNS)


def map_market(raw_market: Market) -> Market:
    name = raw_market.name
    group = "other"
    line = _extract_line(name)

    if is_low_priority(name):
        group = "excluded"
    elif any(keyword in name for keyword in BTTS_KEYWORDS):
        group = "btts"
    elif any(keyword in name for keyword in EURO_HANDICAP_KEYWORDS):
        group = "euro_handicap"
    elif any(keyword in name for keyword in ASIAN_HANDICAP_KEYWORDS):
        group = "asian_handicap"
    elif any(keyword in name for keyword in ASIAN_TOTAL_KEYWORDS):
        group = "asian_total"
    elif is_team_total(name):
        group = "team_total"
    elif any(keyword in name for keyword in TOTAL_KEYWORDS):
        group = "total"

    mapped_outcomes: List[Outcome] = []
    for outcome in raw_market.outcomes:
        side = _map_side(outcome.name)
        mapped_outcomes.append(Outcome(name=outcome.name, price=outcome.price))
        if side:
            mapped_outcomes[-1] = replace(mapped_outcomes[-1], name=outcome.name)

    return Market(
        name=name,
        group=group,
        line=line,
        side=None,
        outcomes=mapped_outcomes,
        raw_name=raw_market.raw_name or raw_market.name,
    )


def map_markets(markets: Iterable[Market]) -> List[Market]:
    return [map_market(market) for market in markets]


def determine_outcome_side(outcome_name: str) -> str | None:
    return _map_side(outcome_name)
