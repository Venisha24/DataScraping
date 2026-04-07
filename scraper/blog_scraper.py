"""
blog_scraper.py
---------------
Scrapes blog posts and extracts structured metadata + content.
Uses requests + BeautifulSoup for HTML parsing.
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Add project root to path
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.chunking import chunk_text
from utils.tagging import assign_topic_tags
from utils.language_detector import detect_language
from scoring.trust_score import calculate_trust_score

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def extract_author(soup: BeautifulSoup) -> str:
    """Try multiple common HTML patterns to find the author."""
    # Meta tags
    for attr in [("name", "author"), ("property", "article:author"),
                 ("name", "twitter:creator"), ("property", "og:author")]:
        tag = soup.find("meta", {attr[0]: attr[1]})
        if tag and tag.get("content"):
            return tag["content"].strip()

    # Common CSS selectors
    selectors = [
        ".author", ".byline", ".post-author", ".entry-author",
        '[rel="author"]', ".author-name", ".writer"
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)

    return "Unknown"


def extract_published_date(soup: BeautifulSoup) -> str:
    """Try multiple patterns to find the published date."""
    # Meta tags
    for attr in [("property", "article:published_time"),
                 ("name", "publish-date"), ("name", "date"),
                 ("property", "og:updated_time")]:
        tag = soup.find("meta", {attr[0]: attr[1]})
        if tag and tag.get("content"):
            raw = tag["content"][:10]   # Take YYYY-MM-DD portion
            return raw

    # time tag
    time_tag = soup.find("time")
    if time_tag:
        return time_tag.get("datetime", time_tag.get_text(strip=True))[:10]

    # Common CSS selectors
    for sel in [".published", ".post-date", ".entry-date", ".date", ".timestamp"]:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)

    return "Unknown"


def extract_article_text(soup: BeautifulSoup) -> str:
    """
    Extract main article text, removing nav, ads, footers, scripts, etc.
    """
    # Remove noise elements
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "noscript", "iframe", "figure"]):
        tag.decompose()

    # Try common article containers
    for sel in ["article", ".post-content", ".entry-content", ".article-body",
                 ".content", "main", "#content", ".blog-post"]:
        el = soup.select_one(sel)
        if el:
            return el.get_text(separator="\n", strip=True)

    # Fallback: get body text
    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)

    return soup.get_text(separator="\n", strip=True)


def scrape_blog(url: str) -> dict:
    """
    Scrape a single blog post URL and return structured data.

    Args:
        url: URL of the blog post.

    Returns:
        Dictionary matching the assignment schema.
    """
    print(f"  Scraping blog: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  ERROR fetching {url}: {e}")
        return _empty_record(url, "blog", error=str(e))

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract title from og:title or <title>
    og_title = soup.find("meta", property="og:title")
    title = og_title["content"] if og_title and og_title.get("content") else ""
    if not title:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

    author = extract_author(soup)
    published_date = extract_published_date(soup)
    content = extract_article_text(soup)
    language = detect_language(content)
    topic_tags = assign_topic_tags(content, title=title)
    chunks = chunk_text(content)

    # Region: try og:locale or accept-language header
    locale_tag = soup.find("meta", property="og:locale")
    region = locale_tag["content"] if locale_tag and locale_tag.get("content") else "Unknown"

    trust = calculate_trust_score(
        source_url=url,
        source_type="blog",
        author=author,
        published_date=published_date,
        content=content,
    )

    return {
        "source_url": url,
        "source_type": "blog",
        "title": title,
        "author": author,
        "published_date": published_date,
        "language": language,
        "region": region,
        "topic_tags": topic_tags,
        "trust_score": trust,
        "content_chunks": chunks,
    }


def scrape_multiple_blogs(urls: list[str]) -> list[dict]:
    """Scrape a list of blog URLs and return list of structured records."""
    results = []
    for url in urls:
        record = scrape_blog(url)
        results.append(record)
    return results


def _empty_record(url: str, source_type: str, error: str = "") -> dict:
    return {
        "source_url": url,
        "source_type": source_type,
        "title": "",
        "author": "Unknown",
        "published_date": "Unknown",
        "language": "en",
        "region": "Unknown",
        "topic_tags": [],
        "trust_score": 0.0,
        "content_chunks": [],
        "error": error,
    }


if __name__ == "__main__":
    
    test_urls = [
        "https://towardsdatascience.com/web-scraping-using-python-1d3e9c5b8f47",
        "https://realpython.com/beautiful-soup-web-scraper-python/",
        "https://www.dataquest.io/blog/web-scraping-python-using-beautiful-soup/",
    ]
    results = scrape_multiple_blogs(test_urls)
    os.makedirs("../output/scraped_data", exist_ok=True)
    with open("../output/scraped_data/blogs.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(results)} blog records.")
