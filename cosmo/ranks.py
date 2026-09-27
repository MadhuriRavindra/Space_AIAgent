"""Stars and space ranks. +1 star per space question, +1 per correct quiz answer."""
from __future__ import annotations

RANKS = [
    (0, "Space Cadet", "🧒"),
    (5, "Rocket Pilot", "🚀"),
    (12, "Mission Specialist", "🛰️"),
    (20, "Space Commander", "🌟"),
    (30, "Astronaut", "👩‍🚀"),
]


def rank_for(stars: int) -> dict:
    """Current rank, the next one and progress (0..1) towards it."""
    stars = max(0, int(stars))
    current = RANKS[0]
    nxt = None
    for i, r in enumerate(RANKS):
        if stars >= r[0]:
            current = r
            nxt = RANKS[i + 1] if i + 1 < len(RANKS) else None
    if nxt:
        span = nxt[0] - current[0]
        progress = (stars - current[0]) / span
    else:
        progress = 1.0
    return {"name": current[1], "emoji": current[2], "stars": stars,
            "next_name": nxt[1] if nxt else None, "next_at": nxt[0] if nxt else None,
            "progress": round(progress, 3)}
