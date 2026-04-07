"""
trust_score.py
--------------
Trust Score Algorithm for evaluating content reliability.

Formula:
    Trust Score = f(author_credibility, citation_count, domain_authority,
                    recency, medical_disclaimer_presence)

Final score is normalized to range [0, 1].
"""

import re
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Known credible domains and organizations (domain authority lookup)
# ---------------------------------------------------------------------------

HIGH_AUTHORITY_DOMAINS = {
    "nih.gov", "pubmed.ncbi.nlm.nih.gov", "who.int", "cdc.gov",
    "nature.com", "science.org", "springer.com", "elsevier.com",
    "harvard.edu", "mit.edu", "stanford.edu", "oxford.ac.uk",
    "bbc.com", "reuters.com", "apnews.com", "theguardian.com",
    "nytimes.com", "washingtonpost.com", "economist.com",
}

MEDIUM_AUTHORITY_DOMAINS = {
    "medium.com", "towardsdatascience.com", "techcrunch.com",
    "wired.com", "forbes.com", "businessinsider.com",
    "wikipedia.org", "youtube.com", "github.com",
}

LOW_AUTHORITY_INDICATORS = [
    "blogspot", "wordpress.com", "weebly", "wix.com",
    "tumblr", "substack.com",
]

SPAM_INDICATORS = [
    "click here", "buy now", "limited offer", "earn money fast",
    "weight loss miracle", "secret revealed", "doctors hate",
]

KNOWN_CREDIBLE_AUTHORS = {
    "world health organization", "who", "cdc", "nih", "mayo clinic",
    "johns hopkins", "harvard medical", "nature", "science",
}

MEDICAL_DISCLAIMER_PATTERNS = [
    r"consult (a|your) (doctor|physician|healthcare provider|medical professional)",
    r"this (article|content|information) is not (medical|professional) advice",
    r"for (medical|health) advice.{0,30}consult",
    r"not intended (to|as).{0,30}(diagnose|treat|cure|prevent)",
    r"medical disclaimer",
    r"always seek.{0,30}(doctor|physician|professional)",
]


# ---------------------------------------------------------------------------
# Individual scoring components
# ---------------------------------------------------------------------------

def score_author_credibility(author: str, source_type: str) -> float:
    """
    Score author credibility based on known organizations and source type.
    Returns 0.0 – 1.0
    """
    if not author or author.strip().lower() in ("unknown", "n/a", ""):
        # Missing author is a red flag
        return 0.2

    author_lower = author.lower()

    
    for credible in KNOWN_CREDIBLE_AUTHORS:
        if credible in author_lower:
            return 1.0

    
    if source_type == "pubmed":
        return 0.85

    
    if source_type == "youtube":
        return 0.55

    
    return 0.5


def score_citation_count(citation_count: int) -> float:
    """
    Score based on citation count (mainly relevant for academic content).
    Returns 0.0 – 1.0
    """
    if citation_count <= 0:
        return 0.3       # No citations: low but not zero
    elif citation_count < 5:
        return 0.5
    elif citation_count < 20:
        return 0.7
    elif citation_count < 100:
        return 0.85
    else:
        return 1.0


def score_domain_authority(source_url: str, content: str = "") -> float:
    """
    Score domain authority based on URL pattern matching.
    Also penalizes for spam content patterns.
    Returns 0.0 – 1.0
    """
    if not source_url:
        return 0.2

    url_lower = source_url.lower()

    # Check high authority
    for domain in HIGH_AUTHORITY_DOMAINS:
        if domain in url_lower:
            return 1.0

    # Check medium authority
    for domain in MEDIUM_AUTHORITY_DOMAINS:
        if domain in url_lower:
            return 0.65

    # Check low authority indicators
    for indicator in LOW_AUTHORITY_INDICATORS:
        if indicator in url_lower:
            # Check for spam in content
            if content:
                spam_hits = sum(1 for s in SPAM_INDICATORS if s in content.lower())
                if spam_hits >= 2:
                    return 0.1   # SEO spam blog
            return 0.3

    # Default for unknown domains
    return 0.45


def score_recency(published_date: str) -> float:
    """
    Score based on how recent the content is.
    Returns 0.0 – 1.0

    Decay schedule:
        < 6 months  → 1.0
        6–12 months → 0.85
        1–2 years   → 0.65
        2–5 years   → 0.4
        > 5 years   → 0.2
        Unknown     → 0.3
    """
    if not published_date or published_date.strip().lower() in ("unknown", "n/a", ""):
        return 0.3

    
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y",
        "%B %d, %Y", "%b %d, %Y", "%Y",
    ]

    parsed_date = None
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(published_date.strip(), fmt)
            break
        except ValueError:
            continue

    if not parsed_date:
        return 0.3

    now = datetime.now()
    age_days = (now - parsed_date).days

    if age_days < 180:
        return 1.0
    elif age_days < 365:
        return 0.85
    elif age_days < 730:
        return 0.65
    elif age_days < 1825:
        return 0.4
    else:
        return 0.2


def score_medical_disclaimer(content: str, source_type: str) -> float:
    """
    Check if medical disclaimer is present when content is health-related.
    Returns 0.0 – 1.0

    Non-medical content gets a neutral score.
    Medical content without disclaimer is penalized.
    """
    if not content:
        return 0.5

    content_lower = content.lower()

    # Check if this is health/medical content
    medical_keywords = [
        "health", "medical", "disease", "treatment", "drug", "medicine",
        "symptom", "diagnosis", "therapy", "clinical", "patient"
    ]
    is_medical = any(kw in content_lower for kw in medical_keywords)

    if not is_medical:
        return 0.8   # Not medical — disclaimer not required

    # Check for disclaimer
    for pattern in MEDICAL_DISCLAIMER_PATTERNS:
        if re.search(pattern, content_lower):
            return 1.0

    # Medical content without disclaimer — penalize
    return 0.2


# ---------------------------------------------------------------------------
# Abuse prevention checks
# ---------------------------------------------------------------------------

def check_abuse(source_url: str, author: str, content: str) -> float:
    """
    Returns a penalty multiplier (0.5 – 1.0).
    1.0 means no abuse detected. Lower values indicate suspected manipulation.
    """
    penalty = 1.0

    if not content:
        return penalty

    content_lower = content.lower()

    # SEO spam detection
    spam_hits = sum(1 for s in SPAM_INDICATORS if s in content_lower)
    if spam_hits >= 3:
        penalty *= 0.5
    elif spam_hits >= 1:
        penalty *= 0.8

    # Fake/suspicious author check
    if author:
        author_lower = author.lower()
        suspicious_patterns = ["admin", "webmaster", "anonymous", "user123", "guest"]
        if any(p in author_lower for p in suspicious_patterns):
            penalty *= 0.7

    # Keyword stuffing detection (same word repeated excessively)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', content_lower)
    if words:
        from collections import Counter
        freq = Counter(words)
        most_common_count = freq.most_common(1)[0][1]
        ratio = most_common_count / len(words)
        if ratio > 0.05:   # One word is >5% of all words → keyword stuffing
            penalty *= 0.75

    return max(penalty, 0.5)   # Floor at 0.5


# ---------------------------------------------------------------------------
# Main trust score function
# ---------------------------------------------------------------------------

def calculate_trust_score(
    source_url: str,
    source_type: str,
    author: str,
    published_date: str,
    content: str,
    citation_count: int = 0,
    weights: dict = None
) -> float:
    """
    Calculate the overall trust score for a piece of content.

    Args:
        source_url:      URL of the content.
        source_type:     One of 'blog', 'youtube', 'pubmed'.
        author:          Author name or channel name.
        published_date:  Publication date string.
        content:         Full text content.
        citation_count:  Number of citations (mainly for academic content).
        weights:         Custom weights dict. Defaults to predefined weights.

    Returns:
        Float between 0.0 and 1.0.
    """

    # Default weights (sum to 1.0)
    if weights is None:
        weights = {
            "author_credibility":        0.25,
            "citation_count":            0.15,
            "domain_authority":          0.25,
            "recency":                   0.20,
            "medical_disclaimer":        0.15,
        }

    # Score each component
    author_score     = score_author_credibility(author, source_type)
    citation_score   = score_citation_count(citation_count)
    domain_score     = score_domain_authority(source_url, content)
    recency_score    = score_recency(published_date)
    disclaimer_score = score_medical_disclaimer(content, source_type)

    # Weighted sum
    raw_score = (
        author_score     * weights["author_credibility"]  +
        citation_score   * weights["citation_count"]      +
        domain_score     * weights["domain_authority"]    +
        recency_score    * weights["recency"]             +
        disclaimer_score * weights["medical_disclaimer"]
    )

    # Apply abuse prevention multiplier
    abuse_multiplier = check_abuse(source_url, author, content)
    final_score = raw_score * abuse_multiplier

    # Clamp to [0, 1]
    return round(min(max(final_score, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# Edge case handler
# ---------------------------------------------------------------------------

def handle_multiple_authors(authors: list[str], source_type: str) -> float:
    """
    When there are multiple authors, average their credibility scores.
    """
    if not authors:
        return score_author_credibility("", source_type)
    scores = [score_author_credibility(a, source_type) for a in authors]
    return round(sum(scores) / len(scores), 4)
