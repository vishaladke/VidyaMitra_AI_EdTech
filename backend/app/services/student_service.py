"""Student service — assignments, tests, progress for the student role.

Handles:
- Listing and viewing assignments (homework/practice)
- Taking and submitting tests with auto-grading (MCQ, true_false)
- Full progress aggregation across all subjects
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, distinct, and_, or_, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assignment, Question, TestAttempt, AssignmentType, QuestionType
from app.models.syllabus import Subject, SyllabusUnit
from app.models.ai import AIConversation, AIMessage
from app.models.user import StudentProfile


# ── Assignments ─────────────────────────────────────────────────

async def get_student_assignments(
    db: AsyncSession,
    student_id: uuid.UUID,
    filter_type: Optional[str] = None,  # "pending" | "completed" | None (all)
) -> list[dict]:
    """Get assignments for a student, with their attempt status."""
    # Get student profile for grade
    profile = await db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == student_id)
    )
    grade = profile.grade if profile else 7

    # Fetch assignments for this student's grade (via subject grade)
    query = (
        select(Assignment, Subject)
        .join(Subject, Assignment.subject_id == Subject.id)
        .where(
            Subject.grade == grade,
            Assignment.is_active == True,
        )
        .order_by(
            Assignment.due_date.desc().nullslast(),
            Assignment.created_at.desc(),
        )
    )

    # Filter to non-test types for assignments page
    if filter_type != "all_types":
        query = query.where(
            Assignment.assignment_type.in_([
                AssignmentType.HOMEWORK, AssignmentType.PRACTICE
            ])
        )

    result = await db.execute(query)
    rows = result.all()

    assignments = []
    for assignment, subject in rows:
        # Check if student has attempted
        attempt = await db.scalar(
            select(TestAttempt).where(
                TestAttempt.student_id == student_id,
                TestAttempt.assignment_id == assignment.id,
            )
        )

        # Count questions
        q_count = await db.scalar(
            select(func.count()).select_from(Question).where(
                Question.assignment_id == assignment.id
            )
        )

        is_submitted = attempt is not None and attempt.submitted_at is not None

        # Apply filter
        if filter_type == "pending" and is_submitted:
            continue
        if filter_type == "completed" and not is_submitted:
            continue

        assignments.append({
            "id": str(assignment.id),
            "title": assignment.title,
            "description": assignment.description,
            "assignment_type": assignment.assignment_type.value,
            "subject_name": subject.name,
            "subject_name_en": subject.name_en,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "max_score": float(assignment.max_score) if assignment.max_score else None,
            "question_count": q_count or 0,
            "is_submitted": is_submitted,
            "score": float(attempt.score) if attempt and attempt.score is not None else None,
            "percentage": float(attempt.percentage) if attempt and attempt.percentage is not None else None,
            "submitted_at": attempt.submitted_at.isoformat() if attempt and attempt.submitted_at else None,
        })

    return assignments


async def get_assignment_detail(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Optional[dict]:
    """Get assignment with questions (without correct answers)."""
    assignment = await db.get(Assignment, assignment_id)
    if not assignment:
        return None

    subject = await db.get(Subject, assignment.subject_id)

    # Get questions
    result = await db.execute(
        select(Question)
        .where(Question.assignment_id == assignment_id)
        .order_by(Question.display_order)
    )
    questions = list(result.scalars().all())

    # Check previous attempt
    attempt = await db.scalar(
        select(TestAttempt).where(
            TestAttempt.student_id == student_id,
            TestAttempt.assignment_id == assignment_id,
        )
    )

    previous = None
    if attempt and attempt.submitted_at:
        previous = {
            "id": str(attempt.id),
            "score": float(attempt.score) if attempt.score is not None else None,
            "max_score": float(attempt.max_score) if attempt.max_score is not None else None,
            "percentage": float(attempt.percentage) if attempt.percentage is not None else None,
            "answers": attempt.answers or {},
            "submitted_at": attempt.submitted_at.isoformat(),
            "is_graded": attempt.is_graded,
        }

    return {
        "id": str(assignment.id),
        "title": assignment.title,
        "description": assignment.description,
        "assignment_type": assignment.assignment_type.value,
        "subject_name": subject.name if subject else "",
        "subject_name_en": subject.name_en if subject else None,
        "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
        "max_score": float(assignment.max_score) if assignment.max_score else None,
        "questions": [
            {
                "id": str(q.id),
                "question_text": q.question_text,
                "question_type": q.question_type.value,
                "options": q.options,
                "marks": float(q.marks),
                "difficulty": q.difficulty.value if q.difficulty else None,
                "display_order": q.display_order,
            }
            for q in questions
        ],
        "previous_attempt": previous,
    }


async def submit_assignment(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    student_id: uuid.UUID,
    answers: dict,  # {question_id: answer_string}
) -> dict:
    """Submit answers for an assignment. Auto-grades MCQ and true_false."""
    assignment = await db.get(Assignment, assignment_id)
    if not assignment:
        raise ValueError("Assignment not found")

    # Get questions
    result = await db.execute(
        select(Question)
        .where(Question.assignment_id == assignment_id)
        .order_by(Question.display_order)
    )
    questions = list(result.scalars().all())

    # Auto-grade
    total_score = 0.0
    max_score = 0.0
    all_graded = True
    results = []

    for q in questions:
        q_id = str(q.id)
        student_answer = answers.get(q_id, "")
        is_correct = None
        earned = 0.0

        if q.question_type in (QuestionType.MCQ, QuestionType.TRUE_FALSE):
            # Auto-gradeable
            is_correct = (
                student_answer.strip().lower() == (q.correct_answer or "").strip().lower()
            )
            earned = float(q.marks) if is_correct else 0.0
        else:
            # Short/long answer — needs teacher review
            all_graded = False

        total_score += earned
        max_score += float(q.marks)

        results.append({
            "id": q_id,
            "question_text": q.question_text,
            "question_type": q.question_type.value,
            "options": q.options,
            "marks": float(q.marks),
            "difficulty": q.difficulty.value if q.difficulty else None,
            "display_order": q.display_order,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "student_answer": student_answer,
            "is_correct": is_correct,
        })

    percentage = round((total_score / max_score * 100), 1) if max_score > 0 else 0.0

    # Check for existing attempt
    existing = await db.scalar(
        select(TestAttempt).where(
            TestAttempt.student_id == student_id,
            TestAttempt.assignment_id == assignment_id,
        )
    )

    if existing:
        # Update existing attempt
        existing.answers = answers
        existing.score = total_score
        existing.max_score = max_score
        existing.percentage = percentage
        existing.submitted_at = datetime.now(timezone.utc)
        existing.is_graded = all_graded
        attempt_id = existing.id
    else:
        # Create new attempt
        attempt = TestAttempt(
            student_id=student_id,
            assignment_id=assignment_id,
            answers=answers,
            score=total_score,
            max_score=max_score,
            percentage=percentage,
            submitted_at=datetime.now(timezone.utc),
            is_graded=all_graded,
        )
        db.add(attempt)
        await db.flush()
        attempt_id = attempt.id

    await db.commit()

    return {
        "success": True,
        "attempt_id": str(attempt_id),
        "score": total_score,
        "max_score": max_score,
        "percentage": percentage,
        "is_graded": all_graded,
        "results": results,
    }


# ── Tests ─────────────────────────────────────────────────────

async def get_student_tests(
    db: AsyncSession,
    student_id: uuid.UUID,
    filter_type: Optional[str] = None,  # "available" | "completed"
) -> list[dict]:
    """Get tests for a student."""
    profile = await db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == student_id)
    )
    grade = profile.grade if profile else 7

    result = await db.execute(
        select(Assignment, Subject)
        .join(Subject, Assignment.subject_id == Subject.id)
        .where(
            Subject.grade == grade,
            Assignment.is_active == True,
            Assignment.assignment_type == AssignmentType.TEST,
        )
        .order_by(Assignment.due_date.desc().nullslast(), Assignment.created_at.desc())
    )
    rows = result.all()

    tests = []
    for assignment, subject in rows:
        attempt = await db.scalar(
            select(TestAttempt).where(
                TestAttempt.student_id == student_id,
                TestAttempt.assignment_id == assignment.id,
            )
        )

        q_count = await db.scalar(
            select(func.count()).select_from(Question).where(
                Question.assignment_id == assignment.id
            )
        )

        is_attempted = attempt is not None and attempt.submitted_at is not None

        if filter_type == "available" and is_attempted:
            continue
        if filter_type == "completed" and not is_attempted:
            continue

        tests.append({
            "id": str(assignment.id),
            "title": assignment.title,
            "description": assignment.description,
            "subject_name": subject.name,
            "subject_name_en": subject.name_en,
            "question_count": q_count or 0,
            "max_score": float(assignment.max_score) if assignment.max_score else None,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "is_attempted": is_attempted,
            "score": float(attempt.score) if attempt and attempt.score is not None else None,
            "percentage": float(attempt.percentage) if attempt and attempt.percentage is not None else None,
            "attempted_at": attempt.submitted_at.isoformat() if attempt and attempt.submitted_at else None,
        })

    return tests


async def get_test_for_taking(
    db: AsyncSession,
    test_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Optional[dict]:
    """Get test questions WITHOUT correct answers (for test-taking)."""
    assignment = await db.get(Assignment, test_id)
    if not assignment or assignment.assignment_type != AssignmentType.TEST:
        return None

    subject = await db.get(Subject, assignment.subject_id)

    result = await db.execute(
        select(Question)
        .where(Question.assignment_id == test_id)
        .order_by(Question.display_order)
    )
    questions = list(result.scalars().all())

    return {
        "id": str(assignment.id),
        "title": assignment.title,
        "description": assignment.description,
        "subject_name": subject.name if subject else "",
        "max_score": float(assignment.max_score) if assignment.max_score else None,
        "questions": [
            {
                "id": str(q.id),
                "question_text": q.question_text,
                "question_type": q.question_type.value,
                "options": q.options,
                "marks": float(q.marks),
                "difficulty": q.difficulty.value if q.difficulty else None,
                "display_order": q.display_order,
            }
            for q in questions
        ],
    }


async def get_test_result(
    db: AsyncSession,
    test_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Optional[dict]:
    """Get test result with correct answers and explanations."""
    attempt = await db.scalar(
        select(TestAttempt).where(
            TestAttempt.student_id == student_id,
            TestAttempt.assignment_id == test_id,
        )
    )
    if not attempt or not attempt.submitted_at:
        return None

    assignment = await db.get(Assignment, test_id)
    subject = await db.get(Subject, assignment.subject_id) if assignment else None

    result = await db.execute(
        select(Question)
        .where(Question.assignment_id == test_id)
        .order_by(Question.display_order)
    )
    questions = list(result.scalars().all())

    question_results = []
    for q in questions:
        q_id = str(q.id)
        student_answer = (attempt.answers or {}).get(q_id, "")
        is_correct = None

        if q.question_type in (QuestionType.MCQ, QuestionType.TRUE_FALSE):
            is_correct = (
                student_answer.strip().lower() == (q.correct_answer or "").strip().lower()
            )

        question_results.append({
            "id": q_id,
            "question_text": q.question_text,
            "question_type": q.question_type.value,
            "options": q.options,
            "marks": float(q.marks),
            "difficulty": q.difficulty.value if q.difficulty else None,
            "display_order": q.display_order,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "student_answer": student_answer,
            "is_correct": is_correct,
        })

    return {
        "attempt_id": str(attempt.id),
        "test_title": assignment.title if assignment else "",
        "subject_name": subject.name if subject else "",
        "score": float(attempt.score) if attempt.score is not None else 0,
        "max_score": float(attempt.max_score) if attempt.max_score is not None else 0,
        "percentage": float(attempt.percentage) if attempt.percentage is not None else 0,
        "is_graded": attempt.is_graded,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "questions": question_results,
    }


# ── Progress ──────────────────────────────────────────────────

async def get_full_progress(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> dict:
    """Get comprehensive progress overview for the progress page."""
    profile = await db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == student_id)
    )
    grade = profile.grade if profile else 7
    streak = profile.streak_days if profile else 0

    # Get all subjects for this grade
    subjects_result = await db.execute(
        select(Subject)
        .where(Subject.grade == grade, Subject.is_active == True)
        .order_by(Subject.display_order)
    )
    subjects = list(subjects_result.scalars().all())

    # Aggregate stats
    total_conversations = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            AIConversation.student_id == student_id
        )
    ) or 0

    total_messages = await db.scalar(
        select(func.count()).select_from(AIMessage).where(
            AIMessage.conversation_id.in_(
                select(AIConversation.id).where(
                    AIConversation.student_id == student_id
                )
            ),
            AIMessage.role == "student",
        )
    ) or 0

    subjects_started = await db.scalar(
        select(func.count(distinct(AIConversation.subject_id))).where(
            AIConversation.student_id == student_id,
            AIConversation.subject_id.isnot(None),
        )
    ) or 0

    # Assignments completed
    assignments_completed = await db.scalar(
        select(func.count()).select_from(TestAttempt).where(
            TestAttempt.student_id == student_id,
            TestAttempt.submitted_at.isnot(None),
            TestAttempt.assignment_id.in_(
                select(Assignment.id).where(
                    Assignment.assignment_type.in_([
                        AssignmentType.HOMEWORK, AssignmentType.PRACTICE
                    ])
                )
            ),
        )
    ) or 0

    # Tests completed
    tests_completed = await db.scalar(
        select(func.count()).select_from(TestAttempt).where(
            TestAttempt.student_id == student_id,
            TestAttempt.submitted_at.isnot(None),
            TestAttempt.assignment_id.in_(
                select(Assignment.id).where(
                    Assignment.assignment_type == AssignmentType.TEST
                )
            ),
        )
    ) or 0

    # Average test score
    avg_score = await db.scalar(
        select(func.avg(TestAttempt.percentage)).where(
            TestAttempt.student_id == student_id,
            TestAttempt.submitted_at.isnot(None),
            TestAttempt.percentage.isnot(None),
        )
    )

    # Per-subject progress
    subject_items = []
    total_units_all = 0
    studied_all = 0

    for subj in subjects:
        total_units = await db.scalar(
            select(func.count()).select_from(SyllabusUnit).where(
                SyllabusUnit.subject_id == subj.id,
                SyllabusUnit.is_active == True,
            )
        ) or 0

        conv_count = await db.scalar(
            select(func.count()).select_from(AIConversation).where(
                AIConversation.student_id == student_id,
                AIConversation.subject_id == subj.id,
            )
        ) or 0

        last_studied = await db.scalar(
            select(func.max(AIConversation.created_at)).where(
                AIConversation.student_id == student_id,
                AIConversation.subject_id == subj.id,
            )
        )

        # Simple completion: conversations as proxy for units studied
        units_studied = min(conv_count, total_units) if total_units > 0 else 0
        completion = round((units_studied / total_units * 100), 1) if total_units > 0 else 0.0

        total_units_all += total_units
        studied_all += units_studied

        subject_items.append({
            "subject_id": str(subj.id),
            "subject_name": subj.name,
            "subject_name_en": subj.name_en,
            "total_units": total_units,
            "units_studied": units_studied,
            "completion_pct": completion,
            "conversation_count": conv_count,
            "last_studied": last_studied.isoformat() if last_studied else None,
        })

    overall_pct = round((studied_all / total_units_all * 100), 1) if total_units_all > 0 else 0.0

    # Recent activity (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    activity_result = await db.execute(
        select(
            func.date_trunc('day', AIConversation.created_at).label('day'),
            func.count().label('count'),
        )
        .where(
            AIConversation.student_id == student_id,
            AIConversation.created_at >= thirty_days_ago,
        )
        .group_by('day')
        .order_by('day')
    )
    activity = [
        {"date": row.day.isoformat() if row.day else None, "count": row.count}
        for row in activity_result.all()
    ]

    return {
        "streak_days": streak,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "subjects_started": subjects_started,
        "total_subjects": len(subjects),
        "overall_completion_pct": overall_pct,
        "assignments_completed": assignments_completed,
        "tests_completed": tests_completed,
        "average_test_score": round(float(avg_score), 1) if avg_score is not None else None,
        "subjects": subject_items,
        "recent_activity": activity,
    }
