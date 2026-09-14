from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class TopicScore(BaseModel):
    topic: str
    score: float = Field(..., ge=0.0, le=10.0, description="Average score out of 10")
    attempts: int = 1

class AnswerEvaluation(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Overall answer score from 0 to 10")
    correctness: float = Field(..., ge=0.0, le=10.0, description="Factual and conceptual accuracy")
    technical_depth: float = Field(..., ge=0.0, le=10.0, description="Depth of technical explanation")
    clarity: float = Field(..., ge=0.0, le=10.0, description="Communication clarity and structure")
    completeness: float = Field(..., ge=0.0, le=10.0, description="Thoroughness of the response")
    confidence: float = Field(default=7.0, ge=0.0, le=10.0, description="Estimated confidence / precision")
    strengths: List[str] = Field(default_factory=list, description="What candidate articulated well")
    weaknesses: List[str] = Field(default_factory=list, description="Flaws, gaps, or inaccuracies")
    missing_concepts: List[str] = Field(default_factory=list, description="Key concepts or keywords missed")
    should_follow_up: bool = Field(default=False, description="Whether an immediate follow-up is warranted")
    follow_up_reason: Optional[str] = Field(default=None, description="Reason if follow-up is suggested")
    recommended_topic: str = Field(..., description="Topic suggested for next step")
    recommended_difficulty: str = Field(default="Medium", description="Suggested difficulty: Easy, Medium, or Hard")

class FinalReport(BaseModel):
    overall_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall composite score out of 100%")
    technical_score: float = Field(..., ge=0.0, le=100.0, description="Technical domain mastery %")
    problem_solving_score: float = Field(..., ge=0.0, le=100.0, description="Analytical reasoning %")
    communication_score: float = Field(..., ge=0.0, le=100.0, description="Clarity and articulation %")
    depth_score: float = Field(..., ge=0.0, le=100.0, description="Technical depth %")
    consistency_score: float = Field(..., ge=0.0, le=100.0, description="Consistency across questions %")
    summary: str = Field(..., description="Concise executive assessment of the candidate")
    strongest_areas: List[str] = Field(default_factory=list, description="Top validated skills/topics")
    needs_improvement: List[str] = Field(default_factory=list, description="Underperforming topics/concepts")
    key_concepts_to_revise: List[str] = Field(default_factory=list, description="Specific terms/theories to study")
    recommended_preparation_plan: List[str] = Field(default_factory=list, description="Actionable 3-step prep guide")
    topic_breakdown: Dict[str, float] = Field(default_factory=dict, description="Topic name to average score out of 10")
