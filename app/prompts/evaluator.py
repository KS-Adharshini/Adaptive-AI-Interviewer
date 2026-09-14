from typing import List, Dict, Any

EVALUATION_SYSTEM = """You are an exacting, objective technical interviewer and assessor evaluating a candidate's response.
Your evaluations must be realistic, calibrated, and rigorous—matching top tech industry standards.

Evaluation Principles:
- 9-10: Masterful, deep, accurate explanation covering edge cases, architectural trade-offs, and practical considerations.
- 7-8: Solid, correct core answer with minor gaps in depth, advanced edge cases, or terminology.
- 5-6: Surface-level understanding or partially correct answer with key omissions.
- 0-4: Incorrect, hand-wavy, hallucinated, or severely misleading answer.

Follow-up criteria:
- Set 'should_follow_up' to true ONLY if the candidate got the high-level intuition right but missed a critical practical mechanism, trade-off, or mathematical/architectural concept that a strong engineer should know.
- If the answer is completely wrong or completely exhaustive, do NOT follow up. Set 'should_follow_up' to false.

Never be sycophantic. Be objective, precise, and constructive.
"""

FINAL_REPORT_SYSTEM = """You are a Principal Engineering Director generating a final diagnostic debrief and preparation roadmap for a candidate who completed an interview.
Provide a clear, candid, and high-value assessment highlighting demonstrated competence, observed blind spots, and concrete technical study items.
"""

def build_evaluation_prompt(
    role: str,
    experience_level: str,
    question: str,
    topic: str,
    difficulty: str,
    candidate_answer: str,
    is_follow_up: bool = False
) -> str:
    """Build prompt for rigorous answer evaluation."""
    prompt = f"""### CANDIDATE PROFILE
- Role: {role}
- Experience Level: {experience_level}
- Assessed Topic: {topic}
- Assessed Difficulty: {difficulty}
- Is Follow-Up Question: {is_follow_up}

### QUESTION POSED
"{question}"

### CANDIDATE'S SUBMITTED ANSWER
"{candidate_answer}"

### TASK
Evaluate the answer thoroughly against industry expectations for a {experience_level} {role}.
Return valid JSON adhering strictly to this schema:
{{
  "overall_score": float (0.0 to 10.0),
  "correctness": float (0.0 to 10.0),
  "technical_depth": float (0.0 to 10.0),
  "clarity": float (0.0 to 10.0),
  "completeness": float (0.0 to 10.0),
  "confidence": float (0.0 to 10.0),
  "strengths": ["list of 1-3 specific strong points articulated"],
  "weaknesses": ["list of 1-3 specific errors, ambiguities, or shallow assertions"],
  "missing_concepts": ["list of key terms, mechanisms, or trade-offs omitted"],
  "should_follow_up": boolean,
  "follow_up_reason": "string explaining what specific concept warrants immediate follow-up, or null",
  "recommended_topic": "suggested topic for the subsequent question",
  "recommended_difficulty": "Easy, Medium, or Hard based on performance"
}}
"""
    return prompt

def build_final_report_prompt(
    role: str,
    experience_level: str,
    interview_type: str,
    total_questions: int,
    session_timeline: List[Dict[str, Any]],
    topic_summary: Dict[str, Dict[str, Any]]
) -> str:
    """Build prompt for comprehensive interview report generation."""
    transcript_blocks = []
    for item in session_timeline:
        q_num = item.get("question_number", 1)
        q_text = item.get("question", "")
        topic = item.get("topic", "")
        diff = item.get("difficulty", "")
        ans = item.get("answer", "")
        score = item.get("score", 0.0)
        strengths = ", ".join(item.get("strengths", []))
        weaknesses = ", ".join(item.get("weaknesses", []))
        missing = ", ".join(item.get("missing_concepts", []))

        block = f"""--- Question {q_num} [{topic} | {diff}] ---
Question: {q_text}
Candidate Answer: {ans}
Score: {score}/10
Strengths: {strengths}
Weaknesses: {weaknesses}
Missing Concepts: {missing}
"""
        transcript_blocks.append(block)

    transcript_str = "\n".join(transcript_blocks)
    topic_str = "\n".join([f"- {t}: Avg {data.get('avg', 0.0)}/10 across {data.get('count', 0)} questions" for t, data in topic_summary.items()])

    prompt = f"""### INTERVIEW SESSION METRICS
- Role: {role}
- Experience Level: {experience_level}
- Type: {interview_type}
- Total Questions Evaluated: {total_questions}

### TOPIC PERFORMANCE
{topic_str}

### FULL INTERVIEW TRANSCRIPT & EVALUATIONS
{transcript_str}

### TASK
Synthesize the entire interview and generate an executive-grade Final Report.
Calculate realistic weighted percentage scores (0.0 to 100.0) for:
- overall_percentage
- technical_score
- problem_solving_score
- communication_score
- depth_score
- consistency_score

Return valid JSON matching this schema:
{{
  "overall_percentage": float,
  "technical_score": float,
  "problem_solving_score": float,
  "communication_score": float,
  "depth_score": float,
  "consistency_score": float,
  "summary": "Professional executive summary of candidate performance (3-5 sentences)",
  "strongest_areas": ["List of 2-4 top demonstrated skills or topics"],
  "needs_improvement": ["List of 2-4 topics or problem-solving areas needing work"],
  "key_concepts_to_revise": ["List of 3-5 specific technical concepts/theories the candidate missed"],
  "recommended_preparation_plan": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
  "topic_breakdown": {{"TopicName": average_score_out_of_10, ...}}
}}
"""
    return prompt
