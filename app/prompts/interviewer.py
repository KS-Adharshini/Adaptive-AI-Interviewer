from typing import List, Dict, Optional, Any

QUESTION_GENERATION_SYSTEM = """You are an elite, professional technical and behavioral interviewer conducting an assessment for a top-tier company.
Your role is to ask ONE sharp, clear, and relevant question calibrated exactly to the candidate's target role, experience level, current difficulty, and interview progression.

CRITICAL INSTRUCTIONS:
1. Formulate EXACTLY ONE interview question.
2. The question must test deep conceptual understanding, practical problem-solving, trade-offs, or real-world system decisions.
3. NEVER repeat or slightly rephrase any question from the previous questions list.
4. If a target weak concept or topic is indicated, design the question to assess that specific area from a practical angle without directly calling the candidate out.
5. If resume context is provided, ground the question in their claimed projects/skills naturally (e.g., 'You mentioned using X in project Y. How did you handle Z?').
6. Keep the tone professional, direct, and concise. Do NOT include preambles, greetings, or conversational filler like 'Great! Now let us move on to...' Just provide the question and metadata.
"""

FOLLOW_UP_SYSTEM = """You are an expert interviewer conducting an adaptive technical interview.
The candidate gave an incomplete, partial, or intriguing answer to the previous question.
Your task is to ask ONE targeted, natural follow-up question that probes deeper into the specific gap, edge case, or trade-off they glossed over.

RULES:
1. Do NOT give generic praise ('Great answer!', 'Good job!', 'Excellent!').
2. Reference their exact line of reasoning concisely and challenge them to address the missing nuance or practical implication.
3. Formulate exactly ONE sharp follow-up question.
4. Keep it professional, calm, and concise.
"""

def build_question_prompt(
    role: str,
    experience_level: str,
    interview_type: str,
    difficulty: str,
    target_topic: str,
    previous_questions: List[str],
    weak_concepts: List[str],
    strong_concepts: List[str],
    resume_context: Optional[str] = None,
    question_number: int = 1,
    total_questions: int = 5
) -> str:
    """Construct structured context for next question generation."""
    prev_q_str = "\n".join([f"- Q{i+1}: {q}" for i, q in enumerate(previous_questions)]) if previous_questions else "None (first question)"
    weak_str = ", ".join(weak_concepts) if weak_concepts else "None detected yet"
    strong_str = ", ".join(strong_concepts) if strong_concepts else "None established yet"

    prompt = f"""### CANDIDATE & SESSION SPECIFICATION
- Target Role: {role}
- Experience Level: {experience_level}
- Interview Type: {interview_type}
- Progress: Question {question_number} of {total_questions}
- Target Topic: {target_topic}
- Target Difficulty: {difficulty}

### PERFORMANCE CONTEXT
- Identified Weak Areas / Missing Concepts: {weak_str}
- Demonstrated Strong Areas: {strong_str}

### PREVIOUS QUESTIONS IN THIS SESSION (DO NOT REPEAT OR DUPLICATE)
{prev_q_str}
"""

    if resume_context:
        prompt += f"""
### CANDIDATE RESUME SUMMARY
{resume_context[:1200]}
(If relevant to the current topic '{target_topic}', personalize the question using their experience.)
"""

    prompt += f"""
### TASK
Generate Question #{question_number} for this candidate.
Respond with JSON matching the following schema:
{{
  "question": "The exact interview question text",
  "topic": "{target_topic}",
  "difficulty": "{difficulty}",
  "target_concept": "Key technical concept being assessed"
}}
"""
    return prompt

def build_follow_up_prompt(
    role: str,
    current_question: str,
    candidate_answer: str,
    missing_concepts: List[str],
    topic: str,
    difficulty: str
) -> str:
    """Construct prompt for targeted follow-up generation."""
    missing_str = ", ".join(missing_concepts) if missing_concepts else "Deeper trade-offs and edge cases"

    prompt = f"""### INTERVIEW CONTEXT
- Role: {role}
- Topic: {topic}
- Difficulty: {difficulty}

### CURRENT QUESTION
"{current_question}"

### CANDIDATE'S ANSWER
"{candidate_answer}"

### IDENTIFIED GAPS / MISSING CONCEPTS
{missing_str}

### TASK
Generate a professional, direct follow-up question that challenges the candidate to elaborate on the missing concepts or technical implications of their answer.
Respond with JSON matching the schema:
{{
  "question": "Follow-up question text",
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "target_concept": "The missing concept or trade-off being probed"
}}
"""
    return prompt
