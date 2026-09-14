import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..config import DATABASE_PATH
from ..models.interview import InterviewConfig, QuestionItem, CandidateAnswer
from ..models.evaluation import AnswerEvaluation, FinalReport

def get_connection() -> sqlite3.Connection:
    """Establish and return a SQLite connection with row factory enabled."""
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Interviews Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interviews (
        id TEXT PRIMARY KEY,
        role TEXT NOT NULL,
        experience TEXT NOT NULL,
        interview_type TEXT NOT NULL,
        difficulty_mode TEXT NOT NULL,
        total_questions INTEGER NOT NULL,
        overall_score REAL DEFAULT 0.0,
        completed INTEGER DEFAULT 0,
        report_json TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Questions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id TEXT PRIMARY KEY,
        interview_id TEXT NOT NULL,
        question_number INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        is_follow_up INTEGER DEFAULT 0,
        target_concept TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (interview_id) REFERENCES interviews (id)
    );
    """)

    # Answers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id TEXT PRIMARY KEY,
        interview_id TEXT NOT NULL,
        question_number INTEGER NOT NULL,
        answer_text TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        FOREIGN KEY (interview_id) REFERENCES interviews (id)
    );
    """)

    # Evaluations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        id TEXT PRIMARY KEY,
        interview_id TEXT NOT NULL,
        question_number INTEGER NOT NULL,
        overall_score REAL NOT NULL,
        correctness REAL NOT NULL,
        technical_depth REAL NOT NULL,
        clarity REAL NOT NULL,
        completeness REAL NOT NULL,
        feedback_json TEXT NOT NULL,
        evaluated_at TEXT NOT NULL,
        FOREIGN KEY (interview_id) REFERENCES interviews (id)
    );
    """)

    conn.commit()
    conn.close()

def save_interview_start(session_id: str, config: InterviewConfig) -> None:
    """Save the initial interview session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO interviews (id, role, experience, interview_type, difficulty_mode, total_questions, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        config.role,
        config.experience_level,
        config.interview_type,
        config.difficulty_mode,
        config.total_questions,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def save_question_record(interview_id: str, q: QuestionItem) -> None:
    """Store generated question."""
    conn = get_connection()
    cursor = conn.cursor()
    q_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO questions (id, interview_id, question_number, question_text, topic, difficulty, is_follow_up, target_concept, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        q_id,
        interview_id,
        q.question_number,
        q.question,
        q.topic,
        q.difficulty,
        1 if q.is_follow_up else 0,
        q.target_concept or "",
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def save_answer_record(interview_id: str, question_number: int, answer_text: str) -> None:
    """Store candidate's submitted answer."""
    conn = get_connection()
    cursor = conn.cursor()
    ans_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO answers (id, interview_id, question_number, answer_text, submitted_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        ans_id,
        interview_id,
        question_number,
        answer_text,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def save_evaluation_record(interview_id: str, question_number: int, eval_data: AnswerEvaluation) -> None:
    """Store evaluation results for an answer."""
    conn = get_connection()
    cursor = conn.cursor()
    eval_id = str(uuid.uuid4())
    feedback_dict = {
        "strengths": eval_data.strengths,
        "weaknesses": eval_data.weaknesses,
        "missing_concepts": eval_data.missing_concepts,
        "should_follow_up": eval_data.should_follow_up,
        "follow_up_reason": eval_data.follow_up_reason,
        "recommended_topic": eval_data.recommended_topic,
        "recommended_difficulty": eval_data.recommended_difficulty
    }
    cursor.execute("""
        INSERT INTO evaluations (id, interview_id, question_number, overall_score, correctness, technical_depth, clarity, completeness, feedback_json, evaluated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        eval_id,
        interview_id,
        question_number,
        eval_data.overall_score,
        eval_data.correctness,
        eval_data.technical_depth,
        eval_data.clarity,
        eval_data.completeness,
        json.dumps(feedback_dict),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def finalize_interview_record(interview_id: str, overall_score: float, report: FinalReport) -> None:
    """Mark an interview as completed with overall score and final report."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE interviews
        SET completed = 1, overall_score = ?, report_json = ?
        WHERE id = ?
    """, (
        overall_score,
        report.model_dump_json(),
        interview_id
    ))
    conn.commit()
    conn.close()

def get_all_interviews() -> List[Dict[str, Any]]:
    """Retrieve all recorded interviews for history view."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, role, experience, interview_type, difficulty_mode, total_questions, overall_score, completed, created_at
        FROM interviews
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_interview_details(interview_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve all detailed records (questions, answers, evaluations, report) for an interview."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
    interview_row = cursor.fetchone()
    if not interview_row:
        conn.close()
        return None
    
    interview = dict(interview_row)
    if interview.get("report_json"):
        try:
            interview["report"] = json.loads(interview["report_json"])
        except Exception:
            interview["report"] = None
    
    cursor.execute("SELECT * FROM questions WHERE interview_id = ? ORDER BY question_number ASC", (interview_id,))
    questions = [dict(q) for q in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM answers WHERE interview_id = ? ORDER BY question_number ASC", (interview_id,))
    answers = {a["question_number"]: dict(a) for a in cursor.fetchall()}
    
    cursor.execute("SELECT * FROM evaluations WHERE interview_id = ? ORDER BY question_number ASC", (interview_id,))
    evaluations = {}
    for ev in cursor.fetchall():
        ev_dict = dict(ev)
        if ev_dict.get("feedback_json"):
            try:
                ev_dict["feedback"] = json.loads(ev_dict["feedback_json"])
            except Exception:
                ev_dict["feedback"] = {}
        evaluations[ev_dict["question_number"]] = ev_dict

    conn.close()

    # Merge into a timeline
    timeline = []
    for q in questions:
        q_num = q["question_number"]
        ans = answers.get(q_num)
        ev = evaluations.get(q_num)
        timeline.append({
            "question": q,
            "answer": ans,
            "evaluation": ev
        })

    return {
        "interview": interview,
        "timeline": timeline
    }
