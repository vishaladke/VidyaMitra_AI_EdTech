"""Student-facing schemas — assignments, tests, progress."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Assignment Schemas ────────────────────────────────────────

class QuestionOut(BaseModel):
    id: str
    question_text: str
    question_type: str  # mcq, short_answer, long_answer, true_false
    options: Optional[dict] = None  # MCQ: {"a": "...", "b": "...", ...}
    marks: float = 1.0
    difficulty: Optional[str] = None
    display_order: int = 0


class QuestionWithAnswer(QuestionOut):
    """Question with correct answer revealed (for results view)."""
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    student_answer: Optional[str] = None
    is_correct: Optional[bool] = None


class AssignmentListItem(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    assignment_type: str  # homework, test, practice
    subject_name: str
    subject_name_en: Optional[str] = None
    due_date: Optional[str] = None
    max_score: Optional[float] = None
    question_count: int = 0
    # Student's attempt info
    is_submitted: bool = False
    score: Optional[float] = None
    percentage: Optional[float] = None
    submitted_at: Optional[str] = None


class AssignmentDetail(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    assignment_type: str
    subject_name: str
    subject_name_en: Optional[str] = None
    due_date: Optional[str] = None
    max_score: Optional[float] = None
    questions: list[QuestionOut] = []
    # Previous attempt
    previous_attempt: Optional[dict] = None


class SubmitAnswersRequest(BaseModel):
    answers: dict = Field(..., description="Map of question_id -> answer string")


class SubmitAnswersResponse(BaseModel):
    success: bool = True
    attempt_id: str
    score: float
    max_score: float
    percentage: float
    is_graded: bool  # False if has long/short answer questions needing teacher review
    results: list[QuestionWithAnswer] = []


# ── Test Schemas ──────────────────────────────────────────────

class TestListItem(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    subject_name: str
    subject_name_en: Optional[str] = None
    question_count: int = 0
    max_score: Optional[float] = None
    due_date: Optional[str] = None
    # Attempt info
    is_attempted: bool = False
    score: Optional[float] = None
    percentage: Optional[float] = None
    attempted_at: Optional[str] = None


class TestForTaking(BaseModel):
    """Test questions WITHOUT correct answers (for test-taking)."""
    id: str
    title: str
    description: Optional[str] = None
    subject_name: str
    max_score: Optional[float] = None
    questions: list[QuestionOut] = []


class TestResultResponse(BaseModel):
    attempt_id: str
    test_title: str
    subject_name: str
    score: float
    max_score: float
    percentage: float
    is_graded: bool
    submitted_at: Optional[str] = None
    questions: list[QuestionWithAnswer] = []


# ── Progress Schemas ──────────────────────────────────────────

class SubjectProgressItem(BaseModel):
    subject_id: str
    subject_name: str
    subject_name_en: Optional[str] = None
    total_units: int = 0
    units_studied: int = 0
    completion_pct: float = 0.0
    conversation_count: int = 0
    last_studied: Optional[str] = None


class ProgressOverview(BaseModel):
    streak_days: int = 0
    total_conversations: int = 0
    total_messages: int = 0
    subjects_started: int = 0
    total_subjects: int = 0
    overall_completion_pct: float = 0.0
    assignments_completed: int = 0
    tests_completed: int = 0
    average_test_score: Optional[float] = None
    subjects: list[SubjectProgressItem] = []
    recent_activity: list[dict] = []  # Last 30 days activity
