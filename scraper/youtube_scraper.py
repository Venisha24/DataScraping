"""
youtube_scraper.py
------------------
Scrapes YouTube video metadata and transcripts.
Uses youtube-transcript-api for transcripts and yt-dlp / requests for metadata.
No API key required for basic metadata extraction.
"""

import json
import re
import requests
import sys
import os

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


def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def fetch_video_metadata(video_id: str) -> dict:
    """
    Fetch video metadata by scraping the YouTube page (no API key needed).
    Extracts: title, channel name, publish date, description.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text
    except requests.RequestException as e:
        print(f"  ERROR fetching YouTube page: {e}")
        return {}

    metadata = {}

    # Title
    title_match = re.search(r'"title":"([^"]+)"', html)
    if title_match:
        metadata["title"] = title_match.group(1).encode().decode("unicode_escape")

    # Channel name
    channel_match = re.search(r'"ownerChannelName":"([^"]+)"', html)
    if channel_match:
        metadata["channel"] = channel_match.group(1)
    else:
        channel_match2 = re.search(r'"author":"([^"]+)"', html)
        if channel_match2:
            metadata["channel"] = channel_match2.group(1)

    # Publish date
    date_match = re.search(r'"publishDate":"([^"]+)"', html)
    if date_match:
        metadata["published_date"] = date_match.group(1)[:10]
    else:
        date_match2 = re.search(r'"uploadDate":"([^"]+)"', html)
        if date_match2:
            metadata["published_date"] = date_match2.group(1)[:10]

    # Description
    desc_match = re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', html)
    if desc_match:
        raw_desc = desc_match.group(1)
        metadata["description"] = raw_desc.replace("\\n", "\n").replace('\\"', '"')

    # View count
    views_match = re.search(r'"viewCount":"(\d+)"', html)
    if views_match:
        metadata["view_count"] = int(views_match.group(1))

    return metadata


def fetch_transcript(video_id: str) -> tuple[str, str]:
    """
    Fetch video transcript using youtube-transcript-api v1.x
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id, languages=["en", "hi", "en-US", "en-GB"])
        full_text = " ".join(entry.text for entry in fetched)
        return full_text, "en"

    except Exception as e:
        print(f"  Transcript unavailable for {video_id}: {e}")
        return "", "en"


def scrape_youtube(url: str) -> dict:
    """
    Scrape a single YouTube video and return structured data.

    Args:
        url: YouTube video URL.

    Returns:
        Dictionary matching the assignment schema.
    """
    print(f"  Scraping YouTube: {url}")

    video_id = extract_video_id(url)
    if not video_id:
        return _empty_record(url, "youtube", error="Could not extract video ID")

    metadata = fetch_video_metadata(video_id)
    transcript_text, lang = fetch_transcript(video_id)

    title = metadata.get("title", "")
    channel = metadata.get("channel", "Unknown")
    published_date = metadata.get("published_date", "Unknown")
    description = metadata.get("description", "")

    # Use description + transcript for content
    combined_content = (description + "\n\n" + transcript_text).strip()

    if not lang or lang == "en":
        lang = detect_language(combined_content) if combined_content else "en"

    topic_tags = assign_topic_tags(combined_content, title=title)

    # Chunk transcript into segments
    content_to_chunk = transcript_text if transcript_text else description
    chunks = chunk_text(content_to_chunk)
    if not chunks and description:
        chunks = chunk_text(description)

    trust = calculate_trust_score(
        source_url=url,
        source_type="youtube",
        author=channel,
        published_date=published_date,
        content=combined_content,
    )

    return {
        "source_url": url,
        "source_type": "youtube",
        "title": title,
        "author": channel,
        "published_date": published_date,
        "language": lang,
        "region": "Unknown",
        "topic_tags": topic_tags,
        "trust_score": trust,
        "content_chunks": chunks,
        "description": description,
        "transcript_available": bool(transcript_text),
    }


def scrape_multiple_youtube(urls: list[str]) -> list[dict]:
    """Scrape a list of YouTube URLs and return list of structured records."""
    results = []
    for url in urls:
        record = scrape_youtube(url)
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
        "description": "",
        "transcript_available": False,
        "error": error,
    }


if __name__ == "__main__":
    test_urls = [
        "https://www.youtube.com/watch?v=XcgH1r4NpuI",  # Web scraping tutorial
        "https://www.youtube.com/watch?v=ng2o98k983k",  # Python requests tutorial
    ]
    results = scrape_multiple_youtube(test_urls)
    os.makedirs("../output/scraped_data", exist_ok=True)
    with open("../output/scraped_data/youtube.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(results)} YouTube records.")
