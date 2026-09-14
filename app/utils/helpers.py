import re
import logging
from difflib import SequenceMatcher
from typing import List, Set

def setup_logger(name: str = "AdaptiveInterviewer") -> logging.Logger:
    """Setup a standard logger with clean formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def normalize_text(text: str) -> str:
    """Lowercase and strip punctuation for comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def extract_keywords(text: str) -> Set[str]:
    """Extract significant tokens ignoring basic English stop words."""
    stop_words = {
        "what", "how", "why", "when", "where", "which", "who", "whom", "whose",
        "can", "could", "would", "should", "is", "are", "was", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "a", "an",
        "the", "and", "but", "if", "or", "because", "as", "until", "while",
        "of", "at", "by", "for", "with", "about", "against", "between", "into",
        "through", "during", "before", "after", "above", "below", "to", "from",
        "up", "down", "in", "out", "on", "off", "over", "under", "again", "further",
        "then", "once", "here", "there", "all", "any", "both", "each", "few",
        "more", "most", "other", "some", "such", "no", "nor", "not", "only",
        "own", "same", "so", "than", "too", "very", "s", "t", "just", "don",
        "now", "explain", "describe", "discuss", "give", "example", "difference"
    }
    tokens = normalize_text(text).split()
    return {w for w in tokens if len(w) > 2 and w not in stop_words}

def is_question_repetitive(new_question: str, past_questions: List[str], threshold: float = 0.65) -> bool:
    """
    Check if a newly generated question is semantically or lexically too similar
    to any previously asked question in this session.
    """
    if not past_questions or not new_question:
        return False

    norm_new = normalize_text(new_question)
    new_kw = extract_keywords(new_question)

    for past in past_questions:
        norm_past = normalize_text(past)
        past_kw = extract_keywords(past)

        # 1. SequenceMatcher ratio
        ratio = SequenceMatcher(None, norm_new, norm_past).ratio()
        if ratio >= threshold:
            return True

        # 2. Significant keyword Jaccard overlap
        if new_kw and past_kw:
            overlap = len(new_kw.intersection(past_kw))
            union = len(new_kw.union(past_kw))
            jaccard = overlap / union if union > 0 else 0
            if jaccard >= 0.55:
                return True

    return False

def format_score(score: float, max_score: float = 10.0) -> str:
    """Format numerical score cleanly."""
    return f"{score:.1f} / {max_score:.0f}"

def get_score_badge_class(score: float, max_score: float = 10.0) -> str:
    """Return styling class for score display."""
    pct = (score / max_score) * 100.0
    if pct >= 80:
        return "score-high"
    elif pct >= 55:
        return "score-mid"
    return "score-low"

def clean_html(html_str: str) -> str:
    """
    Strips leading whitespace from every line to ensure CommonMark/Markdown
    never interprets HTML lines as 4-space indented code blocks.
    """
    return "\n".join(line.strip() for line in html_str.strip().splitlines() if line.strip())

def get_difficulty_badge_class(difficulty: str) -> str:
    """Return styling class for difficulty tag."""
    d = difficulty.strip().lower()
    if d == "easy":
        return "diff-easy"
    elif d == "hard":
        return "diff-hard"
    return "diff-medium"
