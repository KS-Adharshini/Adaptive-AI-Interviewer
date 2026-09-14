import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or current directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
dotenv_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=dotenv_path)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "interview_platform.db"))

# Application Defaults
DEFAULT_QUESTIONS_COUNT = int(os.getenv("DEFAULT_QUESTIONS_COUNT", "5"))
MIN_QUESTIONS = 3
MAX_QUESTIONS = 12

# Standard Roles
AVAILABLE_ROLES = [
    "Software Engineer",
    "Machine Learning Engineer",
    "Data Scientist",
    "Data Analyst",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "AI/ML Engineer",
    "Custom..."
]

EXPERIENCE_LEVELS = [
    "Fresher / Student (0-1 yrs)",
    "Junior (1-3 yrs)",
    "Mid-Level (3-5 yrs)",
    "Senior (5+ yrs)"
]

INTERVIEW_TYPES = [
    "Technical",
    "Behavioral",
    "Mixed (Technical + Behavioral)"
]

DIFFICULTY_MODES = [
    "Adaptive (Recommended)",
    "Easy",
    "Medium",
    "Hard"
]
