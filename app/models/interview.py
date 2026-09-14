from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class InterviewConfig(BaseModel):
    role: str = Field(..., description="Target job role")
    experience_level: str = Field(..., description="Candidate experience level")
    interview_type: str = Field(default="Technical", description="Technical, Behavioral, or Mixed")
    difficulty_mode: str = Field(default="Adaptive (Recommended)", description="Adaptive or fixed difficulty")
    total_questions: int = Field(default=5, ge=3, le=15, description="Number of questions in session")
    resume_context: Optional[str] = Field(default=None, description="Extracted resume text or summary if uploaded")

class QuestionItem(BaseModel):
    question_number: int
    question: str
    topic: str
    difficulty: str  # "Easy", "Medium", "Hard"
    is_follow_up: bool = False
    follow_up_context: Optional[str] = None
    target_concept: Optional[str] = None

class CandidateAnswer(BaseModel):
    question_number: int
    answer_text: str
    submitted_at: datetime = Field(default_factory=datetime.now)

class TopicMetric(BaseModel):
    topic: str
    total_score: float = 0.0
    attempts: int = 0
    weak_concepts: List[str] = Field(default_factory=list)

    @property
    def average_score(self) -> float:
        return round(self.total_score / self.attempts, 1) if self.attempts > 0 else 0.0

class InterviewSession(BaseModel):
    session_id: str
    config: InterviewConfig
    created_at: datetime = Field(default_factory=datetime.now)
    completed: bool = False
    current_difficulty: str = "Medium"
    questions: List[QuestionItem] = Field(default_factory=list)
    answers: List[CandidateAnswer] = Field(default_factory=list)
    topic_metrics: Dict[str, TopicMetric] = Field(default_factory=dict)
    consecutive_high: int = 0
    consecutive_low: int = 0
    overall_score: Optional[float] = None
