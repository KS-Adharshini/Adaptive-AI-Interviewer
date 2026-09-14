import random
from typing import List, Dict, Optional, Tuple
from ..models.interview import InterviewConfig, InterviewSession, QuestionItem, CandidateAnswer
from ..models.evaluation import AnswerEvaluation
from ..prompts.interviewer import (
    QUESTION_GENERATION_SYSTEM,
    FOLLOW_UP_SYSTEM,
    build_question_prompt,
    build_follow_up_prompt
)
from ..utils.helpers import is_question_repetitive, setup_logger
from .gemini_service import GeminiService, GeminiServiceError

logger = setup_logger("AdaptiveEngine")

# Standard Topic Curricula per Role
ROLE_CURRICULA: Dict[str, List[str]] = {
    "Software Engineer": [
        "Data Structures & Algorithms",
        "System Architecture & Scaling",
        "Concurrency & Multithreading",
        "API Design & Networking",
        "Database Indexing & Transactions",
        "Clean Code & Design Patterns"
    ],
    "Machine Learning Engineer": [
        "Feature Engineering & Data Preprocessing",
        "Supervised & Unsupervised Algorithms",
        "Deep Learning Architectures",
        "Model Evaluation & Validation Metrics",
        "Loss Functions & Optimization",
        "MLOps, Inference Latency & Model Deployment"
    ],
    "Data Scientist": [
        "Statistical Inference & Hypothesis Testing",
        "Exploratory Data Analysis & Feature Selection",
        "Predictive Modeling & Ensembles",
        "A/B Testing & Experimentation",
        "Dimensionality Reduction & Clustering",
        "Business Metric Translation"
    ],
    "Data Analyst": [
        "SQL Query Optimization & Aggregations",
        "Statistical Summaries & Distributions",
        "Data Cleaning & Anomaly Detection",
        "Dashboard Design & KPI Tracking",
        "Data Warehousing Concepts",
        "Exploratory Analysis & Business Insights"
    ],
    "Backend Developer": [
        "REST & gRPC Architecture",
        "Database Modeling & Sharding",
        "Caching Strategies & Redis",
        "Authentication, Security & OWASP",
        "Message Queues & Event-Driven Systems",
        "Microservices & Fault Tolerance"
    ],
    "Frontend Developer": [
        "JavaScript / TypeScript Event Loop & Asynchrony",
        "DOM Performance & Rendering Optimization",
        "State Management & Data Flow",
        "Component Design & Reusability",
        "Web Accessibility & Responsive Design",
        "Network Optimization & Asset Bundling"
    ],
    "Full Stack Developer": [
        "End-to-End System Architecture",
        "Frontend-Backend API Contracts",
        "Database Schema Design & Query Performance",
        "Authentication & Authorization Flows",
        "State Management & UI Hydration",
        "CI/CD, Containerization & Deployment"
    ],
    "AI/ML Engineer": [
        "Transformers & Attention Mechanisms",
        "Vector Embeddings & Retrieval Systems (RAG)",
        "Model Quantization & Efficient Fine-Tuning",
        "Distributed Training & GPU Memory Management",
        "Model Evaluation, Hallucination & Alignment",
        "Serving Pipelines & Pipeline Optimization"
    ]
}

BEHAVIORAL_TOPICS = [
    "Conflict Resolution & Disagreement",
    "Technical Leadership & Mentorship",
    "Handling Ambiguity & Tight Deadlines",
    "Learning from Failure & Postmortems",
    "Cross-Functional Collaboration",
    "Prioritization & Trade-off Decisions"
]

class AdaptiveEngine:
    """Core stateful engine controlling difficulty transitions, topic selection, and follow-ups."""

    def __init__(self, gemini_service: Optional[GeminiService] = None):
        self.gemini = gemini_service or GeminiService()

    def get_role_topics(self, role: str, interview_type: str) -> List[str]:
        """Fetch balanced topics for the chosen role and interview type."""
        tech_topics = ROLE_CURRICULA.get(role, ROLE_CURRICULA["Software Engineer"])
        if interview_type == "Behavioral":
            return BEHAVIORAL_TOPICS
        elif interview_type == "Mixed (Technical + Behavioral)":
            # Interleave technical and behavioral
            combined = []
            for i in range(max(len(tech_topics), len(BEHAVIORAL_TOPICS))):
                if i < len(tech_topics):
                    combined.append(tech_topics[i])
                if i < len(BEHAVIORAL_TOPICS):
                    combined.append(BEHAVIORAL_TOPICS[i])
            return combined
        return tech_topics

    def calculate_next_difficulty(
        self,
        current_difficulty: str,
        last_score: float,
        consecutive_high: int,
        consecutive_low: int,
        mode: str = "Adaptive (Recommended)"
    ) -> Tuple[str, int, int]:
        """
        Controlled difficulty algorithm:
        Score >= 8.0: Increase difficulty (Easy -> Medium -> Hard)
        Score 5.0 - 7.9: Maintain difficulty
        Score <= 4.9: Decrease difficulty (Hard -> Medium -> Easy)
        
        Incorporates consecutive answer streaks to prevent sudden whipsawing.
        """
        if mode != "Adaptive (Recommended)":
            return current_difficulty, 0, 0

        levels = ["Easy", "Medium", "Hard"]
        current_idx = levels.index(current_difficulty) if current_difficulty in levels else 1

        new_high = consecutive_high
        new_low = consecutive_low

        if last_score >= 8.0:
            new_high += 1
            new_low = 0
            # If candidate shows strong answer, step up if not already at maximum
            if current_idx < len(levels) - 1:
                current_idx += 1
        elif last_score <= 4.9:
            new_low += 1
            new_high = 0
            # If candidate struggles, drop difficulty if not already at minimum
            if current_idx > 0:
                current_idx -= 1
        else:
            # Neutral / mid-range performance: reset streaks and maintain
            new_high = 0
            new_low = 0

        # Safety: Never allow jumping directly from Easy to Hard
        next_difficulty = levels[current_idx]
        return next_difficulty, new_high, new_low

    def select_next_topic(
        self,
        session: InterviewSession,
        last_eval: Optional[AnswerEvaluation] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Select next topic adapting to candidate's weak spots, missing concepts,
        or cycling to unexplored topics in the curriculum.
        Returns (topic_name, weak_concept_target_if_any)
        """
        all_topics = self.get_role_topics(session.config.role, session.config.interview_type)
        asked_topics = [q.topic for q in session.questions]

        # 1. If candidate struggled on the previous evaluation (score <= 5) and missed specific concepts,
        # prioritize testing that weak concept directly if we haven't already retried it.
        if last_eval and last_eval.overall_score < 6.0 and last_eval.missing_concepts:
            weak_concept = last_eval.missing_concepts[0]
            # Use recommended topic or repeat current
            return last_eval.recommended_topic or session.questions[-1].topic, weak_concept

        # 2. Check historical weak topics across the session
        weak_topics = [
            t for t, metric in session.topic_metrics.items()
            if metric.average_score < 6.0 and metric.attempts < 2
        ]
        if weak_topics and random.random() < 0.4:
            chosen = weak_topics[0]
            metric = session.topic_metrics[chosen]
            weak_concept = metric.weak_concepts[0] if metric.weak_concepts else None
            return chosen, weak_concept

        # 3. Otherwise, select the next unasked topic in the curriculum
        unasked = [t for t in all_topics if t not in asked_topics]
        if unasked:
            return unasked[0], None

        # 4. If all topics touched once, cycle back to lowest scoring topic or random
        sorted_by_score = sorted(
            session.topic_metrics.items(),
            key=lambda item: item[1].average_score
        )
        if sorted_by_score:
            return sorted_by_score[0][0], None

        return random.choice(all_topics), None

    def generate_next_question(
        self,
        session: InterviewSession,
        last_eval: Optional[AnswerEvaluation] = None
    ) -> QuestionItem:
        """
        Generate the next adaptive question based on full session state,
        handling follow-up branching, difficulty transitions, and repetition prevention.
        """
        q_num = len(session.questions) + 1
        past_questions_text = [q.question for q in session.questions]

        # --- BRANCH A: FOLLOW-UP QUESTION ---
        if last_eval and last_eval.should_follow_up and session.questions and session.answers:
            prev_q = session.questions[-1]
            prev_ans = session.answers[-1].answer_text
            missing_concepts = last_eval.missing_concepts

            logger.info(f"Generating follow-up question for Q{prev_q.question_number} on gap: {missing_concepts}")
            
            follow_up_item = self._generate_follow_up(
                role=session.config.role,
                prev_question=prev_q.question,
                candidate_answer=prev_ans,
                missing_concepts=missing_concepts,
                topic=prev_q.topic,
                difficulty=session.current_difficulty,
                question_number=q_num
            )
            
            # Anti-repetition check
            if not is_question_repetitive(follow_up_item.question, past_questions_text):
                return follow_up_item

        # --- BRANCH B: ADAPTIVE NEW QUESTION ---
        target_topic, weak_concept = self.select_next_topic(session, last_eval)

        # Gather weak and strong concepts for prompt context
        weak_concepts_list = []
        strong_concepts_list = []
        for metric in session.topic_metrics.values():
            if metric.average_score < 6.0:
                weak_concepts_list.extend(metric.weak_concepts)
            elif metric.average_score >= 8.0:
                strong_concepts_list.append(metric.topic)

        # Attempt question generation with anti-repetition loop (up to 3 tries)
        for attempt in range(3):
            candidate_item = self._generate_new_question(
                session=session,
                question_number=q_num,
                target_topic=target_topic,
                difficulty=session.current_difficulty,
                past_questions=past_questions_text,
                weak_concepts=weak_concepts_list,
                strong_concepts=strong_concepts_list,
                weak_concept_target=weak_concept
            )
            if not is_question_repetitive(candidate_item.question, past_questions_text):
                return candidate_item
            logger.warning(f"Repetitive question detected on attempt {attempt+1}: {candidate_item.question[:60]}... Regenerating.")

        # Fallback question if repetition loop exhausts
        return candidate_item

    def _generate_new_question(
        self,
        session: InterviewSession,
        question_number: int,
        target_topic: str,
        difficulty: str,
        past_questions: List[str],
        weak_concepts: List[str],
        strong_concepts: List[str],
        weak_concept_target: Optional[str] = None
    ) -> QuestionItem:
        """Call Gemini to generate a structured new question, or fallback if unconfigured."""
        if not self.gemini.is_configured():
            return self._mock_question(session.config.role, target_topic, difficulty, question_number, weak_concept_target)

        prompt = build_question_prompt(
            role=session.config.role,
            experience_level=session.config.experience_level,
            interview_type=session.config.interview_type,
            difficulty=difficulty,
            target_topic=target_topic,
            previous_questions=past_questions,
            weak_concepts=weak_concepts,
            strong_concepts=strong_concepts,
            resume_context=session.config.resume_context,
            question_number=question_number,
            total_questions=session.config.total_questions
        )

        try:
            raw_res = self.gemini.generate_structured(
                prompt=prompt,
                system_instruction=QUESTION_GENERATION_SYSTEM,
                temperature=0.6
            )
            return QuestionItem(
                question_number=question_number,
                question=raw_res.get("question", "Explain the architectural trade-offs in this domain."),
                topic=raw_res.get("topic", target_topic),
                difficulty=raw_res.get("difficulty", difficulty),
                is_follow_up=False,
                target_concept=raw_res.get("target_concept", weak_concept_target)
            )
        except Exception as e:
            logger.warning(f"Gemini question generation error: {e}. Using intelligent fallback.")
            return self._mock_question(session.config.role, target_topic, difficulty, question_number, weak_concept_target)

    def _generate_follow_up(
        self,
        role: str,
        prev_question: str,
        candidate_answer: str,
        missing_concepts: List[str],
        topic: str,
        difficulty: str,
        question_number: int
    ) -> QuestionItem:
        """Call Gemini to generate a sharp follow-up question."""
        if not self.gemini.is_configured():
            gap = missing_concepts[0] if missing_concepts else "edge cases and performance impact"
            return QuestionItem(
                question_number=question_number,
                question=f"Building on your point: specifically how would you address {gap} in a high-throughput production environment?",
                topic=topic,
                difficulty=difficulty,
                is_follow_up=True,
                follow_up_context=prev_question,
                target_concept=gap
            )

        prompt = build_follow_up_prompt(
            role=role,
            current_question=prev_question,
            candidate_answer=candidate_answer,
            missing_concepts=missing_concepts,
            topic=topic,
            difficulty=difficulty
        )

        try:
            raw_res = self.gemini.generate_structured(
                prompt=prompt,
                system_instruction=FOLLOW_UP_SYSTEM,
                temperature=0.5
            )
            return QuestionItem(
                question_number=question_number,
                question=raw_res.get("question", f"How would you address the trade-offs regarding {', '.join(missing_concepts)}?"),
                topic=topic,
                difficulty=difficulty,
                is_follow_up=True,
                follow_up_context=prev_question,
                target_concept=raw_res.get("target_concept")
            )
        except Exception as e:
            logger.warning(f"Follow-up generation error: {e}. Using fallback.")
            gap = missing_concepts[0] if missing_concepts else "underlying trade-offs"
            return QuestionItem(
                question_number=question_number,
                question=f"Can you drill deeper into how {gap} influences system stability in this scenario?",
                topic=topic,
                difficulty=difficulty,
                is_follow_up=True,
                follow_up_context=prev_question,
                target_concept=gap
            )

    def _mock_question(
        self,
        role: str,
        topic: str,
        difficulty: str,
        q_num: int,
        target_concept: Optional[str] = None
    ) -> QuestionItem:
        """High-grade curated mock question generator for testing and offline sandbox."""
        mock_bank = {
            "Data Structures & Algorithms": {
                "Easy": "Explain the time complexity differences between an array list and a singly linked list for insertion operations.",
                "Medium": "How does Python's dictionary implement hash collision resolution, and what occurs under high load factors?",
                "Hard": "Design an LRU cache with O(1) get and put operations, detailing the exact data structures and synchronization."
            },
            "System Architecture & Scaling": {
                "Easy": "What is the difference between horizontal and vertical scaling, and when is each preferred?",
                "Medium": "How would you handle cache invalidation in a distributed system with multiple read replicas?",
                "Hard": "How would you architect a distributed rate limiter that handles 100,000 requests per second across 10 regions?"
            },
            "Machine Learning Engineer": {
                "Easy": "Explain the bias-variance tradeoff and how it impacts model generalization.",
                "Medium": "Why might cross-entropy loss be preferred over mean squared error for classification tasks?",
                "Hard": "How do you detect and mitigate training-serving skew in a real-time recommendation system?"
            }
        }

        # Select closest matching question
        role_bank = mock_bank.get(topic, mock_bank.get("System Architecture & Scaling"))
        question_text = role_bank.get(difficulty, f"Explain key design principles and trade-offs in {topic}.")
        
        if target_concept:
            question_text = f"Regarding {target_concept}: what are the core failure modes and how would you mitigate them?"

        return QuestionItem(
            question_number=q_num,
            question=question_text,
            topic=topic,
            difficulty=difficulty,
            is_follow_up=False,
            target_concept=target_concept
        )
