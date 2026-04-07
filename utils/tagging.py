"""
tagging.py
----------
Automatic topic tagging using keyword extraction (no external ML libraries needed).
Uses TF-IDF-style scoring with a predefined topic taxonomy for mapping.
"""

import re
from collections import Counter

# Common stopwords to filter out
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "its", "this", "that", "was",
    "are", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall", "can",
    "not", "no", "nor", "so", "yet", "both", "either", "neither", "as",
    "if", "then", "than", "too", "very", "just", "about", "also", "into",
    "through", "during", "before", "after", "above", "below", "between",
    "each", "more", "most", "other", "some", "such", "only", "own", "same",
    "while", "he", "she", "they", "we", "you", "i", "me", "him", "her",
    "us", "them", "what", "which", "who", "whom", "when", "where", "why",
    "how", "all", "any", "few", "many", "much", "our", "their", "your",
    "his", "my", "these", "those", "there", "here", "up", "out", "over",
    "under", "again", "further", "once", "s", "t", "re", "ve", "ll", "d"
}

# Topic taxonomy: maps keywords to topic labels
TOPIC_TAXONOMY = {
    "AI": ["artificial intelligence", "ai", "machine learning", "deep learning", "neural network",
           "nlp", "natural language", "computer vision", "llm", "gpt", "chatbot", "automation"],
    "Machine Learning": ["machine learning", "ml", "supervised", "unsupervised", "classification",
                         "regression", "clustering", "random forest", "xgboost", "scikit", "model training"],
    "Healthcare": ["healthcare", "health", "medical", "medicine", "clinical", "patient", "hospital",
                   "disease", "treatment", "diagnosis", "therapy", "doctor", "pharmaceutical"],
    "Data Science": ["data science", "data analysis", "analytics", "statistics", "visualization",
                     "pandas", "numpy", "matplotlib", "jupyter", "dataset", "big data"],
    "Web Scraping": ["web scraping", "scraping", "crawler", "beautifulsoup", "selenium", "requests",
                     "html", "parsing", "scraper", "data collection", "web crawling"],
    "Python": ["python", "flask", "django", "fastapi", "pip", "virtualenv", "conda"],
    "Research": ["research", "study", "paper", "journal", "pubmed", "abstract", "citation",
                 "peer reviewed", "academic", "experiment", "findings", "methodology"],
    "Finance": ["finance", "stock", "market", "investment", "economy", "trading", "crypto",
                "bitcoin", "blockchain", "bank", "revenue", "profit"],
    "Technology": ["technology", "tech", "software", "hardware", "cloud", "aws", "azure",
                   "kubernetes", "docker", "devops", "api", "microservices"],
    "Education": ["education", "learning", "course", "tutorial", "training", "university",
                  "student", "teacher", "curriculum", "online learning", "mooc"],
    "Environment": ["environment", "climate", "sustainability", "green", "carbon", "energy",
                    "renewable", "solar", "wind", "pollution", "ecosystem"],
    "Cybersecurity": ["cybersecurity", "security", "hacking", "malware", "encryption", "firewall",
                      "vulnerability", "phishing", "privacy", "data breach"],
}


def extract_keywords(text: str, top_n: int = 20) -> list[str]:
    """
    Extract top N keywords from text using word frequency (simple TF approach).
    Filters out stopwords and short tokens.
    """
    if not text:
        return []

    # Lowercase and extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in STOPWORDS]

    # Count frequency
    freq = Counter(filtered)
    top_keywords = [word for word, _ in freq.most_common(top_n)]
    return top_keywords


def assign_topic_tags(text: str, title: str = "", max_tags: int = 5) -> list[str]:
    """
    Assign topic tags to content based on keyword matching against a taxonomy.

    Args:
        text: Main body of the content.
        title: Title or headline (weighted more heavily).
        max_tags: Maximum number of tags to return.

    Returns:
        List of topic tag strings.
    """
    combined = (title + " " + title + " " + text).lower()  # title counted twice for weight

    tag_scores = {}

    for topic, keywords in TOPIC_TAXONOMY.items():
        score = 0
        for kw in keywords:
            # Count occurrences of each keyword
            score += combined.count(kw)
        if score > 0:
            tag_scores[topic] = score

    # Sort by score descending
    sorted_tags = sorted(tag_scores, key=tag_scores.get, reverse=True)
    return sorted_tags[:max_tags]
