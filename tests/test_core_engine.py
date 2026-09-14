import os
import sys
import uuid

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.interview import InterviewConfig, InterviewSession, QuestionItem, CandidateAnswer
from app.models.evaluation import AnswerEvaluation, FinalReport
from app.database.db import (
    init_db,
    save_interview_start,
    save_question_record,
    save_answer_record,
    save_evaluation_record,
    finalize_interview_record,
    get_all_interviews,
    get_interview_details
)
from app.services.interview_engine import AdaptiveEngine
from app.services.evaluator import EvaluatorService
from app.utils.helpers import is_question_repetitive

def run_tests():
    print("=== 1. Testing Database Initialization ===")
    init_db()
    print("Database tables initialized successfully.")

    print("\n=== 2. Testing Anti-Repetition Logic ===")
    past_q = [
        "Explain the bias-variance tradeoff in supervised learning.",
        "How do you implement an LRU cache in Python?"
    ]
    assert is_question_repetitive("Explain the bias-variance tradeoff and its effect on models.", past_q) is True
    assert is_question_repetitive("What is the difference between TCP and UDP?", past_q) is False
    print("Repetition detection working as expected.")

    print("\n=== 3. Testing Adaptive Difficulty Algorithm ===")
    engine = AdaptiveEngine()
    # High score (9.0) on Easy -> Medium
    diff, h, l = engine.calculate_next_difficulty("Easy", 9.0, 0, 0)
    assert diff == "Medium"
    assert h == 1
    # High score on Medium -> Hard
    diff2, h2, l2 = engine.calculate_next_difficulty("Medium", 8.5, h, l)
    assert diff2 == "Hard"
    # Low score (3.5) on Hard -> Medium
    diff3, h3, l3 = engine.calculate_next_difficulty("Hard", 3.5, 0, 0)
    assert diff3 == "Medium"
    assert l3 == 1
    print("Adaptive difficulty state transitions validated.")

    print("\n=== 4. Testing End-to-End Session Persistence ===")
    session_id = str(uuid.uuid4())
    config = InterviewConfig(
        role="Machine Learning Engineer",
        experience_level="Junior (1-3 yrs)",
        interview_type="Technical",
        difficulty_mode="Adaptive (Recommended)",
        total_questions=3
    )
    save_interview_start(session_id, config)

    # Question 1
    q1 = QuestionItem(
        question_number=1,
        question="What is the difference between L1 and L2 regularization?",
        topic="Supervised Learning",
        difficulty="Easy"
    )
    save_question_record(session_id, q1)

    # Answer 1
    ans_text = "L1 regularization adds absolute weights and produces sparse coefficients, whereas L2 adds squared weights and penalizes extreme values."
    save_answer_record(session_id, 1, ans_text)

    # Evaluation 1
    evaluator = EvaluatorService()
    eval1 = evaluator.evaluate_answer(config.role, config.experience_level, q1, ans_text)
    save_evaluation_record(session_id, 1, eval1)
    print(f"Q1 evaluated with score: {eval1.overall_score}/10")

    # Session mock state for final report
    session = InterviewSession(session_id=session_id, config=config)
    session.questions.append(q1)
    session.answers.append(CandidateAnswer(question_number=1, answer_text=ans_text))
    final_report = evaluator.generate_final_report(session)
    finalize_interview_record(session_id, final_report.overall_percentage, final_report)

    # Fetch back
    details = get_interview_details(session_id)
    assert details is not None
    assert details["interview"]["role"] == "Machine Learning Engineer"
    assert len(details["timeline"]) == 1
    assert details["timeline"][0]["question"]["question_text"] == q1.question
    print(f"Retrieved interview details successfully: overall score = {details['interview']['overall_score']}%")

    print("\n=== ALL CORE ENGINE TESTS PASSED! ===")

if __name__ == "__main__":
    run_tests()
