<<<<<<< HEAD
# Data Scraping & Trust Scoring System

A multi-source web scraping pipeline with an automated content trust scoring algorithm.

---

## Project Structure

```
project/
├── main.py                      # Main runner — run this to scrape all sources
├── requirements.txt             # Python dependencies
├── scraper/
│   ├── blog_scraper.py          # Scrapes blog posts
│   ├── youtube_scraper.py       # Scrapes YouTube videos + transcripts
│   └── pubmed_scraper.py        # Scrapes PubMed academic articles
├── scoring/
│   └── trust_score.py           # Trust score algorithm
├── utils/
│   ├── chunking.py              # Text chunking utility
│   ├── tagging.py               # Automatic topic tagging
│   └── language_detector.py    # Language detection
└── output/
    └── scraped_data/
        ├── blogs.json           # Blog scraping results
        ├── youtube.json         # YouTube scraping results
        ├── pubmed.json          # PubMed scraping results
        └── scraped_data.json    # Combined output (all 6 sources)
```

---

## Tools and Libraries Used

| Library | Purpose |
|---|---|
| `requests` | HTTP requests to fetch web pages |
| `beautifulsoup4` | HTML parsing for blog scraping |
| `lxml` | Fast HTML/XML parser (used by BeautifulSoup) |
| `langdetect` | Automatic language detection |
| `youtube-transcript-api` | Fetch YouTube video transcripts |
| `biopython` | NCBI Entrez API for PubMed article fetching |

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure sources

Open `main.py` and edit the `SOURCES` section:

```python
BLOG_URLS = [
    "https://realpython.com/beautiful-soup-web-scraper-python/",
    "https://research.google/blog vibe-coding-xr-accelerating-ai-xr-prototyping-with-xr-blocks-and-gemini/",
    "https://www.scrapehero.com/web-scraping-blog-posts/",
]

YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=D1eL1EnxXXQ",   
    "https://www.youtube.com/watch?v=ng2o98k983k",  
]

PUBMED_IDS = [
    "38355097",   # PubMed ID (PMID) or full URL
]

ENTREZ_EMAIL = "venishapchampaneri24@gmail.com"  # Required by NCBI
```

### 3. Run the scraper

```bash
python main.py
```

Output files will be saved to `output/scraped_data/`.

---

## Scraping Approach

### Blog Scraping
- Uses `requests` to fetch the HTML page
- `BeautifulSoup` parses the HTML
- Tries multiple CSS selectors and meta tags to extract author, date, and content
- Removes noise: nav bars, footers, ads, scripts
- Falls back gracefully when fields are missing

### YouTube Scraping
- Extracts video ID from URL
- Fetches the YouTube page HTML and uses regex to extract metadata (no API key needed)
- Uses `youtube-transcript-api` to fetch transcripts (auto-generated or manual)
- Falls back gracefully if transcript is unavailable

### PubMed Scraping
- Uses Biopython's `Entrez` module to call the NCBI Entrez API
- Fetches article in XML format and parses: title, authors, journal, abstract, MeSH keywords
- Respects NCBI's rate limit (0.5s delay between requests)

---

## Trust Score Design

**Formula:**

```
Trust Score = (
    author_credibility   × 0.25 +
    citation_count       × 0.15 +
    domain_authority     × 0.25 +
    recency              × 0.20 +
    medical_disclaimer   × 0.15
) × abuse_multiplier
```

Each component is scored 0–1. The final score is clamped to [0, 1].

### Component Breakdown

| Component | How it's scored |
|---|---|
| **Author Credibility** | Known organizations score 1.0; PubMed authors 0.85; unknown 0.2 |
| **Citation Count** | 0 = 0.3, 1–4 = 0.5, 5–19 = 0.7, 20–99 = 0.85, 100+ = 1.0 |
| **Domain Authority** | High-authority domains (nih.gov, bbc.com) = 1.0; medium = 0.65; low = 0.3 |
| **Recency** | <6 months = 1.0; 6–12 months = 0.85; 1–2 years = 0.65; >5 years = 0.2 |
| **Medical Disclaimer** | Non-medical content = 0.8; medical with disclaimer = 1.0; medical without = 0.2 |

### Abuse Prevention
- SEO spam content detection (keyword stuffing, clickbait phrases)
- Suspicious author names (admin, anonymous) penalized
- Low-authority domains with spam content get a 0.1 floor score
- Keyword stuffing detected via word frequency ratio

---

## Limitations

- YouTube metadata extraction relies on regex from the page HTML, which may break if YouTube changes its page structure. For production use, the YouTube Data API v3 is recommended.
- PubMed citation counts are approximated via PubMed Central links and may not reflect actual citation counts.
- Language detection (`langdetect`) requires at least ~20 characters and may misidentify short content.
- Some blogs block scraping via bot detection (Cloudflare, CAPTCHAs). Selenium can be used as a fallback.
- Trust score is rule-based, not ML-based; it reflects the quality of the rules rather than true credibility.

---

## Output Format

Each scraped source is stored as a JSON object:

```json
{
  "source_url": "https://example.com/article",
  "source_type": "blog",
  "title": "Article Title",
  "author": "Author Name",
  "published_date": "2024-03-15",
  "language": "en",
  "region": "en_US",
  "topic_tags": ["AI", "Machine Learning", "Healthcare"],
  "trust_score": 0.7234,
  "content_chunks": [
    "Paragraph 1...",
    "Paragraph 2...",
    "Paragraph 3..."
  ]
}
```
=======
# DataScraping
Built a Python-based multi-source scraper to extract and structure data from blogs, YouTube, and PubMed. Implemented metadata extraction, topic tagging, and content chunking. Designed a trust scoring system evaluating source reliability using credibility, recency, citations, and domain authority.
>>>>>>> 66e3c870c83426ecb1209d84c88b0d3897fce05e
