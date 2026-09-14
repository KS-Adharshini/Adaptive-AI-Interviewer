"""Utility package"""
from .helpers import (
    is_question_repetitive,
    format_score,
    get_score_badge_class,
    get_difficulty_badge_class,
    setup_logger,
    clean_html
)

__all__ = [
    "is_question_repetitive",
    "format_score",
    "get_score_badge_class",
    "get_difficulty_badge_class",
    "setup_logger",
    "clean_html"
]
