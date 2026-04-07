"""
language_detector.py
--------------------
Detects the language of a given text.
Uses langdetect library with a fallback to 'en' if detection fails.
"""

def detect_language(text: str) -> str:
    """
    Detect the language of the given text.

    Args:
        text: Input text to detect language from.

    Returns:
        ISO 639-1 language code (e.g., 'en', 'fr', 'de').
        Returns 'en' as default if detection fails.
    """
    if not text or len(text.strip()) < 20:
        return "en"

    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "en"
