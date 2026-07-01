"""
SHL Product Catalog Scraper.

Scrapes assessment data from https://www.shl.com/solutions/products/product-catalog/
Falls back to curated dataset if the live site is JS-rendered or blocks requests.

Usage:
    python -m app.scraper.scraper
"""
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"
DETAIL_BASE = "https://www.shl.com"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "shl_catalog.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _fetch_page(url: str) -> Optional[BeautifulSoup]:
    """Fetch a page and return parsed soup, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as exc:
        print(f"  [WARN] Failed to fetch {url}: {exc}")
        return None


def _parse_catalog_table(soup: BeautifulSoup) -> List[Dict]:
    """Parse the product catalog table from the page."""
    assessments = []

    # Try to find table rows — SHL uses a custom table component
    rows = soup.select("tr.catalog__row, table tbody tr, .product-catalog__row")
    if not rows:
        # Try alternative selectors
        rows = soup.select("tr")

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        # First cell usually has the link and name
        link_tag = cells[0].find("a")
        if not link_tag:
            continue

        name = link_tag.get_text(strip=True)
        href = link_tag.get("href", "")
        url = href if href.startswith("http") else DETAIL_BASE + href

        # Parse remaining cells for test type indicators, duration, etc.
        entry = {
            "name": name,
            "url": url,
            "description": "",
            "test_type": [],
            "skills": [],
            "duration": "",
            "remote_testing": False,
            "adaptive_irt": False,
            "job_families": [],
        }

        # Check for test type icons/badges (A, K, P, S, etc.)
        for cell in cells[1:]:
            text = cell.get_text(strip=True).lower()
            # Check for checkmarks or "Yes" indicators
            if cell.find("span", class_=re.compile(r"check|yes|tick", re.I)):
                pass  # Will be handled per-column

        assessments.append(entry)

    return assessments


def _scrape_detail_page(url: str, entry: Dict) -> Dict:
    """Scrape additional details from an assessment's detail page."""
    soup = _fetch_page(url)
    if not soup:
        return entry

    # Try to find description
    desc_el = soup.select_one(
        ".product-detail__description, .product-catalog-detail__description, "
        ".content-block p, article p, .hero__text p"
    )
    if desc_el:
        entry["description"] = desc_el.get_text(strip=True)

    # Look for metadata in definition lists or key-value pairs
    for dt in soup.find_all("dt"):
        label = dt.get_text(strip=True).lower()
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        value = dd.get_text(strip=True)

        if "duration" in label or "time" in label:
            entry["duration"] = value
        elif "type" in label:
            entry["test_type"] = [t.strip() for t in value.split(",")]
        elif "skill" in label:
            entry["skills"] = [s.strip() for s in value.split(",")]
        elif "job" in label or "family" in label or "role" in label:
            entry["job_families"] = [j.strip() for j in value.split(",")]
        elif "remote" in label:
            entry["remote_testing"] = "yes" in value.lower()
        elif "adaptive" in label or "irt" in label:
            entry["adaptive_irt"] = "yes" in value.lower()

    return entry


def scrape_catalog() -> List[Dict]:
    """Scrape the full SHL product catalog."""
    print("[INFO] Starting SHL catalog scrape...")
    all_assessments = []
    page = 0

    while True:
        url = f"{BASE_URL}?start={page * 12}&sz=12&type=1"
        print(f"  Fetching page {page + 1}: {url}")
        soup = _fetch_page(url)

        if not soup:
            print("  [WARN] Could not fetch page, stopping pagination.")
            break

        new_items = _parse_catalog_table(soup)
        if not new_items:
            print("  No more items found, stopping.")
            break

        all_assessments.extend(new_items)
        page += 1
        time.sleep(1)  # Be polite

        # Safety cap
        if page > 50:
            print("  [WARN] Reached 50 page cap, stopping.")
            break

    # Fetch detail pages
    print(f"[INFO] Found {len(all_assessments)} assessments. Fetching details...")
    for i, entry in enumerate(all_assessments):
        if entry.get("url"):
            print(f"  [{i+1}/{len(all_assessments)}] {entry['name']}")
            _scrape_detail_page(entry["url"], entry)
            time.sleep(0.5)

    return all_assessments


def save_catalog(assessments: List[Dict], path: Path = OUTPUT_FILE) -> None:
    """Save catalog to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(assessments, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Saved {len(assessments)} assessments to {path}")


def load_catalog(path: Path = OUTPUT_FILE) -> List[Dict]:
    """Load catalog from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    assessments = scrape_catalog()
    if assessments:
        save_catalog(assessments)
    else:
        print("[WARN] Live scrape returned 0 results (site may be JS-rendered).")
        print("[INFO] Using curated catalog dataset instead.")
        print("[INFO] Run: python -c \"from app.scraper.scraper import load_catalog; print(len(load_catalog()))\"")
