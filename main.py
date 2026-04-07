"""
main.py
-------
Main runner script that ties together all scrapers and produces output JSON files.

Usage:
    python main.py

Edit the SOURCES section below to specify which URLs to scrape.
"""

import json
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.blog_scraper import scrape_multiple_blogs
from scraper.youtube_scraper import scrape_multiple_youtube
from scraper.pubmed_scraper import scrape_multiple_pubmed




BLOG_URLS = [
    "https://realpython.com/beautiful-soup-web-scraper-python/",
    "https://research.google/blog/vibe-coding-xr-accelerating-ai-xr-prototyping-with-xr-blocks-and-gemini/",
    "https://www.scrapehero.com/web-scraping-blog-posts/",
]

YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=D1eL1EnxXXQ",   
    "https://www.youtube.com/watch?v=ng2o98k983k", 
]

PUBMED_IDS = [
    "38355097",   
]


ENTREZ_EMAIL = "venishapchampaneri24@gmail.com"

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "scraped_data")

# =============================================================================


def save_json(data: list[dict], filename: str):
    """Save data to a JSON file in the output directory."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved → {filepath} ({len(data)} records)")


def main():
    print("=" * 60)
    print("   Multi-Source Data Scraper")
    print("=" * 60)

    # --- Blogs ---
    print("\n[1/3] Scraping blog posts...")
    blogs = scrape_multiple_blogs(BLOG_URLS)
    save_json(blogs, "blogs.json")

    # --- YouTube ---
    print("\n[2/3] Scraping YouTube videos...")
    youtube = scrape_multiple_youtube(YOUTUBE_URLS)
    save_json(youtube, "youtube.json")

    # --- PubMed ---
    print("\n[3/3] Scraping PubMed articles...")
    pubmed = scrape_multiple_pubmed(PUBMED_IDS, email=ENTREZ_EMAIL)
    save_json(pubmed, "pubmed.json")

    # --- Combined output ---
    all_sources = blogs + youtube + pubmed
    save_json(all_sources, "scraped_data.json")

    print("\n" + "=" * 60)
    print(f"  Done! Total sources scraped: {len(all_sources)}")
    print(f"  Output saved to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
