"""
pubmed_scraper.py
-----------------
Scrapes PubMed articles using the NCBI Entrez API (via Biopython).
No API key required for basic usage (rate limited to 3 requests/sec).
"""

import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.chunking import chunk_text
from utils.tagging import assign_topic_tags
from utils.language_detector import detect_language
from scoring.trust_score import calculate_trust_score


def parse_pubmed_id(url_or_id: str) -> str:
    """
    Extract PubMed ID (PMID) from a URL or return as-is if it's already an ID.

    Examples:
        "https://pubmed.ncbi.nlm.nih.gov/38234567/" → "38234567"
        "38234567" → "38234567"
    """
    import re
    match = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", url_or_id)
    if match:
        return match.group(1)
    
    if url_or_id.strip().isdigit():
        return url_or_id.strip()
    return url_or_id.strip()


def fetch_pubmed_article(pmid: str, email: str = "student@example.com") -> dict:
    """
    Fetch a PubMed article by PMID using Biopython's Entrez module.

    Args:
        pmid:  PubMed ID string.
        email: Your email (required by NCBI to identify users).

    Returns:
        Dictionary with article fields.
    """
    try:
        from Bio import Entrez
        import xml.etree.ElementTree as ET
    except ImportError:
        raise ImportError("Biopython not installed. Run: pip install biopython")

    Entrez.email = email

    # Fetch article in XML format
    try:
        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="xml", retmode="xml")
        records = Entrez.read(handle)
        handle.close()
    except Exception as e:
        print(f"  ERROR fetching PubMed article {pmid}: {e}")
        return {}

    if not records.get("PubmedArticle"):
        return {}

    article_data = records["PubmedArticle"][0]
    medline = article_data.get("MedlineCitation", {})
    article = medline.get("Article", {})

    # --- Title ---
    title = str(article.get("ArticleTitle", ""))

    # --- Authors ---
    authors = []
    author_list = article.get("AuthorList", [])
    for author in author_list:
        last = author.get("LastName", "")
        fore = author.get("ForeName", "")
        if last:
            authors.append(f"{fore} {last}".strip() if fore else last)

    # --- Journal ---
    journal_info = article.get("Journal", {})
    journal_name = str(journal_info.get("Title", ""))

    # --- Publication Date ---
    pub_date = "Unknown"
    journal_issue = journal_info.get("JournalIssue", {})
    pub_date_raw = journal_issue.get("PubDate", {})
    year = pub_date_raw.get("Year", "")
    month = pub_date_raw.get("Month", "")
    day = pub_date_raw.get("Day", "")
    if year:
        pub_date = year
        if month:
            pub_date = f"{year}-{month}"
        if month and day:
            pub_date = f"{year}-{month}-{day}"

    # --- Abstract ---
    abstract = ""
    abstract_obj = article.get("Abstract", {})
    abstract_text = abstract_obj.get("AbstractText", [])
    if isinstance(abstract_text, list):
        abstract = " ".join(str(a) for a in abstract_text)
    elif abstract_text:
        abstract = str(abstract_text)

    # --- Keywords / MeSH Terms ---
    keywords = []
    mesh_list = medline.get("MeshHeadingList", [])
    for mesh in mesh_list:
        descriptor = mesh.get("DescriptorName", "")
        if descriptor:
            keywords.append(str(descriptor))

    # --- Citation Count (approximated via PubMed Central links) ---
    # NCBI doesn't directly expose citation counts; default to 0
    citation_count = 0
    try:
        link_handle = Entrez.elink(dbfrom="pubmed", db="pmc", id=pmid)
        link_records = Entrez.read(link_handle)
        link_handle.close()
        pmc_links = link_records[0].get("LinkSetDb", [])
        for link_set in pmc_links:
            if link_set.get("LinkName") == "pubmed_pmc_refs":
                citation_count = len(link_set.get("Link", []))
    except Exception:
        pass

    return {
        "title": title,
        "authors": authors,
        "journal": journal_name,
        "published_date": pub_date,
        "abstract": abstract,
        "keywords": keywords,
        "citation_count": citation_count,
    }


def scrape_pubmed(url_or_id: str, email: str = "venishapchampaneri24@gmail.com") -> dict:
    """
    Scrape a PubMed article and return structured data.

    Args:
        url_or_id: PubMed URL or PMID.
        email:     Your email for NCBI Entrez API.

    Returns:
        Dictionary matching the assignment schema.
    """
    print(f"  Scraping PubMed: {url_or_id}")

    pmid = parse_pubmed_id(url_or_id)
    source_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    article = fetch_pubmed_article(pmid, email=email)
    if not article:
        return _empty_record(source_url, error="Could not fetch article")

    title = article.get("title", "")
    authors = article.get("authors", [])
    journal = article.get("journal", "")
    published_date = article.get("published_date", "Unknown")
    abstract = article.get("abstract", "")
    keywords = article.get("keywords", [])
    citation_count = article.get("citation_count", 0)

    # Author string
    author_str = ", ".join(authors) if authors else "Unknown"

    # Language detection on abstract
    language = detect_language(abstract) if abstract else "en"

    # Topic tags: combine keywords with auto-tagging
    auto_tags = assign_topic_tags(abstract, title=title)
    combined_tags = list(dict.fromkeys(keywords[:3] + auto_tags))[:6]

    # Chunk the abstract
    chunks = chunk_text(abstract, max_words=100)

    trust = calculate_trust_score(
        source_url=source_url,
        source_type="pubmed",
        author=author_str,
        published_date=published_date,
        content=abstract,
        citation_count=citation_count,
    )

    return {
        "source_url": source_url,
        "source_type": "pubmed",
        "title": title,
        "author": author_str,
        "journal": journal,
        "published_date": published_date,
        "language": language,
        "region": "Unknown",
        "topic_tags": combined_tags,
        "trust_score": trust,
        "content_chunks": chunks,
        "citation_count": citation_count,
    }


def scrape_multiple_pubmed(urls_or_ids: list[str], email: str = "student@example.com") -> list[dict]:
    """Scrape a list of PubMed URLs/IDs with a small delay to respect NCBI rate limits."""
    results = []
    for item in urls_or_ids:
        record = scrape_pubmed(item, email=email)
        results.append(record)
        time.sleep(0.5)   
    return results


def _empty_record(url: str, error: str = "") -> dict:
    return {
        "source_url": url,
        "source_type": "pubmed",
        "title": "",
        "author": "Unknown",
        "journal": "",
        "published_date": "Unknown",
        "language": "en",
        "region": "Unknown",
        "topic_tags": [],
        "trust_score": 0.0,
        "content_chunks": [],
        "citation_count": 0,
        "error": error,
    }


if __name__ == "__main__":
    
    test_ids = [
        "https://pubmed.ncbi.nlm.nih.gov/38234567/",
    ]
    results = scrape_multiple_pubmed(test_ids, email="student@example.com")
    os.makedirs("../output/scraped_data", exist_ok=True)
    with open("../output/scraped_data/pubmed.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(results)} PubMed records.")
