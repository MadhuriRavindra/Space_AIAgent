"""Real space pictures from NASA's free APIs."""
from __future__ import annotations

import re

import requests

# Words a child might use -> a NASA search that returns a good, recognisable picture.
# Checked in order, so more specific entries come first.
IMAGE_QUERIES = [
    (("black hole",), "black hole event horizon"),
    (("space station", "iss"), "International Space Station orbit"),
    (("spacesuit", "space suit", "spacewalk"), "spacewalk astronaut"),
    (("astronaut",), "astronaut spacewalk"),
    (("rocket", "launch"), "rocket launch"),
    (("milky way",), "Milky Way galaxy"),
    (("galaxy", "galaxies"), "spiral galaxy Hubble"),
    (("nebula",), "nebula Hubble"),
    (("saturn",), "Saturn rings Cassini"),
    (("jupiter",), "Jupiter Great Red Spot"),
    (("mars",), "Mars planet globe"),
    (("venus",), "Venus planet"),
    (("mercury",), "Mercury planet MESSENGER"),
    (("uranus",), "Uranus planet Voyager"),
    (("neptune",), "Neptune Voyager"),
    (("pluto",), "Pluto New Horizons"),
    (("comet",), "comet"),
    (("asteroid",), "asteroid Bennu"),
    (("eclipse",), "solar eclipse"),
    (("moon",), "full Moon"),
    (("sun", "solar"), "Sun solar dynamics observatory"),
    (("earth",), "Earth from space blue marble"),
    (("star",), "star cluster Hubble"),
]


def image_query_for(question: str) -> str | None:
    q = " " + re.sub(r"[^a-z ]", " ", (question or "").lower()) + " "
    for words, query in IMAGE_QUERIES:
        for w in words:
            # whole-word match so "sunday" doesn't match "sun" and "starfish" doesn't match "star"
            if re.search(rf"\b{re.escape(w)}(s|es)?\b", q):
                return query
    return None


def parse_search(data: dict) -> dict | None:
    for item in (data or {}).get("collection", {}).get("items", []):
        links = [lk for lk in item.get("links", []) if lk.get("render") == "image" or "href" in lk]
        meta = (item.get("data") or [{}])[0]
        if links and meta.get("media_type", "image") == "image":
            return {"url": links[0]["href"], "title": meta.get("title", "NASA image"),
                    "nasa_id": meta.get("nasa_id", "")}
    return None


def search_image(query: str) -> dict | None:
    """First matching photo from images.nasa.gov (no API key needed)."""
    try:
        r = requests.get("https://images-api.nasa.gov/search",
                         params={"q": query, "media_type": "image", "page_size": 5}, timeout=6)
        r.raise_for_status()
        return parse_search(r.json())
    except Exception as e:  # noqa: BLE001
        print("NASA image search failed:", e)
        return None


def get_apod(api_key: str = "DEMO_KEY") -> dict | None:
    """NASA's Astronomy Picture of the Day."""
    try:
        r = requests.get("https://api.nasa.gov/planetary/apod",
                         params={"api_key": api_key or "DEMO_KEY", "thumbs": "true"}, timeout=8)
        r.raise_for_status()
        d = r.json()
        image = d.get("url") if d.get("media_type") == "image" else d.get("thumbnail_url")
        return {"title": d.get("title", ""), "explanation": d.get("explanation", ""),
                "image": image, "link": d.get("hdurl") or d.get("url"),
                "date": d.get("date", ""), "media_type": d.get("media_type", "image"),
                "copyright": (d.get("copyright") or "").strip()}
    except Exception as e:  # noqa: BLE001
        print("APOD failed:", e)
        return None
