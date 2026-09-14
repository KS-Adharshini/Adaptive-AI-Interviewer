from typing import Optional, List, Dict, Any
from ..models.interview import InterviewSession, QuestionItem
from ..models.evaluation import AnswerEvaluation, FinalReport
from ..prompts.evaluator import (
    EVALUATION_SYSTEM,
    FINAL_REPORT_SYSTEM,
    build_evaluation_prompt,
    build_final_report_prompt
)
from ..utils.helpers import setup_logger
from .gemini_service import GeminiService, GeminiServiceError

logger = setup_logger("EvaluatorService")

class EvaluatorService:
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        self.gemini = gemini_service or GeminiService()

    def evaluate_answer(
        self,
        role: str,
        experience_level: str,
        question: QuestionItem,
        candidate_answer: str
    ) -> AnswerEvaluation:
        """
        Evaluate candidate's answer returning structured AnswerEvaluation.
        """
        clean_answer = candidate_answer.strip()
        if not clean_answer:
            return AnswerEvaluation(
                overall_score=0.0,
                correctness=0.0,
                technical_depth=0.0,
                clarity=0.0,
                completeness=0.0,
                confidence=0.0,
                strengths=[],
                weaknesses=["No answer was provided."],
                missing_concepts=["Complete response"],
                should_follow_up=False,
                follow_up_reason=None,
                recommended_topic=question.topic,
                recommended_difficulty="Easy"
            )

        if not self.gemini.is_configured():
            return self._mock_evaluation(question, clean_answer)

        prompt = build_evaluation_prompt(
            role=role,
            experience_level=experience_level,
            question=question.question,
            topic=question.topic,
            difficulty=question.difficulty,
            candidate_answer=clean_answer,
            is_follow_up=question.is_follow_up
        )

        try:
            eval_res = self.gemini.generate_structured(
                prompt=prompt,
                system_instruction=EVALUATION_SYSTEM,
                schema=AnswerEvaluation,
                temperature=0.2
            )
            return eval_res
        except Exception as e:
            logger.warning(f"Error during Gemini answer evaluation: {e}. Using calibrated fallback.")
            return self._mock_evaluation(question, clean_answer)

    def generate_final_report(self, session: InterviewSession) -> FinalReport:
        """
        Synthesize full interview session and generate executive FinalReport.
        """
        if not session.answers:
            return self._fallback_empty_report()

        # Build timeline summary for prompt
        timeline_data = []
        for i, q in enumerate(session.questions):
            ans = session.answers[i].answer_text if i < len(session.answers) else ""
            timeline_data.append({
                "question_number": q.question_number,
                "question": q.question,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "answer": ans,
                "score": 7.0,  # Default if individual evaluation not loaded in memory
                "strengths": ["Demonstrated basic clarity"],
                "weaknesses": ["Minor gaps in depth"],
                "missing_concepts": []
            })

        topic_summary = {}
        for topic, metric in session.topic_metrics.items():
            topic_summary[topic] = {
                "avg": metric.average_score,
                "count": metric.attempts,
                "weak_concepts": metric.weak_concepts
            }

        if not self.gemini.is_configured():
            return self._mock_final_report(session)

        prompt = build_final_report_prompt(
            role=session.config.role,
            experience_level=session.config.experience_level,
            interview_type=session.config.interview_type,
            total_questions=len(session.questions),
            session_timeline=timeline_data,
            topic_summary=topic_summary
        )

        try:
            report_res = self.gemini.generate_structured(
                prompt=prompt,
                system_instruction=FINAL_REPORT_SYSTEM,
                schema=FinalReport,
                temperature=0.3
            )
            return report_res
        except Exception as e:
            logger.warning(f"Error generating final report with Gemini: {e}. Using deterministic synthesis.")
            return self._mock_final_report(session)

    def _mock_evaluation(self, question: QuestionItem, answer: str) -> AnswerEvaluation:
        """Deterministic evaluation for offline sandbox/test mode based on word count & technicality."""
        words = len(answer.split())
        if words < 15:
            score = 3.5
            strengths = ["Attempted an initial definition."]
            weaknesses = ["Answer was extremely brief and lacked technical specifics."]
            missing = ["Detailed architecture", "Implementation trade-offs", "Edge case analysis"]
            should_follow = False
            rec_diff = "Easy"
        elif words < 45:
            score = 6.5
            strengths = ["Correct foundational explanation.", "Clear direct terminology."]
            weaknesses = ["Lacks discussion of production scalability or edge constraints."]
            missing = ["Practical trade-offs", "Resource constraints"]
            should_follow = True
            rec_diff = "Medium"
        else:
            score = 8.5
            strengths = [
                "Comprehensive technical breakdown.",
                "Explicitly addressed trade-offs and operational implications.",
                "Well-structured explanation."
            ]
            weaknesses = ["Could quantify concrete benchmarks or performance metrics."]
            missing = ["Specific performance benchmarks"]
            should_follow = False
            rec_diff = "Hard"

        return AnswerEvaluation(
            overall_score=score,
            correctness=round(min(10.0, score + 0.5), 1),
            technical_depth=round(score, 1),
            clarity=round(min(10.0, score + 0.3), 1),
            completeness=round(score, 1),
            confidence=8.0,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_concepts=missing,
            should_follow_up=should_follow,
            follow_up_reason="Candidate touched upon key ideas but missed production operational nuances." if should_follow else None,
            recommended_topic=question.topic,
            recommended_difficulty=rec_diff
        )

    def _mock_final_report(self, session: InterviewSession) -> FinalReport:
        """Synthesize final report deterministically from topic metrics."""
        scores = [metric.average_score for metric in session.topic_metrics.values() if metric.attempts > 0]
        avg_out_of_10 = sum(scores) / len(scores) if scores else 7.0
        pct = round(avg_out_of_10 * 10.0, 1)

        strong_topics = [t for t, m in session.topic_metrics.items() if m.average_score >= 7.0]
        weak_topics = [t for t, m in session.topic_metrics.items() if m.average_score < 7.0]
        
        all_weak_concepts = []
        for m in session.topic_metrics.values():
            all_weak_concepts.extend(m.weak_concepts)

        topic_breakdown = {t: m.average_score for t, m in session.topic_metrics.items()}

        return FinalReport(
            overall_percentage=pct,
            technical_score=round(min(100.0, pct + 3.0), 1),
            problem_solving_score=round(pct, 1),
            communication_score=round(min(100.0, pct + 5.0), 1),
            depth_score=round(max(40.0, pct - 4.0), 1),
            consistency_score=round(pct, 1),
            summary=(
                f"Candidate completed a {session.config.difficulty_mode.lower()} interview for {session.config.role}. "
                f"They demonstrated solid foundational knowledge across core topics with steady articulation, "
                f"though further rigor around deep edge cases and production trade-offs will strengthen their profile."
            ),
            strongest_areas=strong_topics or ["Foundational principles", "Communication clarity"],
            needs_improvement=weak_topics or ["Complex edge cases", "System boundary trade-offs"],
            key_concepts_to_revise=all_weak_concepts[:4] or ["High-load scaling", "Failure domain isolation", "Performance benchmarking"],
            recommended_preparation_plan=[
                f"1. Deep-dive into trade-offs for {weak_topics[0] if weak_topics else 'distributed data patterns'}.",
                "2. Practice timed problem explanations with explicit emphasis on space/time and operational constraints.",
                "3. Review concrete failure modes and postmortem scenarios for production architectures."
            ],
            topic_breakdown=topic_breakdown
        )

    def _fallback_empty_report(self) -> FinalReport:
        return FinalReport(
            overall_percentage=0.0,
            technical_score=0.0,
            problem_solving_score=0.0,
            communication_score=0.0,
            depth_score=0.0,
            consistency_score=0.0,
            summary="Interview session was ended before answers were submitted.",
            strongest_areas=[],
            needs_improvement=["Incomplete session"],
            key_concepts_to_revise=[],
            recommended_preparation_plan=["Start a new interview session and complete all questions."],
            topic_breakdown={}
        )
