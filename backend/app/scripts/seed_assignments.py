"""Seed assignments + tests with Marathi MCQ questions for student demo.

Run after seed_dev_users and seed_syllabus:
    cd backend
    python -m app.scripts.seed_assignments

Creates:
    - 3 homework assignments (गणित, विज्ञान, मराठी) with MCQ questions
    - 2 tests (गणित, विज्ञान) with mixed MCQ questions
    - 1 pre-submitted attempt so progress page shows data
"""
import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import select
from app.database import async_session_factory as async_session
from app.models.syllabus import Subject
from app.models.user import User, UserRole
from app.models.assessment import (
    Assignment, Question, TestAttempt,
    AssignmentType, QuestionType, DifficultyLevel,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Marathi MCQ Question Banks ────────────────────────────────

MATH_QUESTIONS = [
    {
        "text": "2 + 3 × 4 = ?",
        "type": QuestionType.MCQ,
        "options": {"a": "20", "b": "14", "c": "12", "d": "10"},
        "answer": "b",
        "explanation": "गणिताच्या BODMAS नियमानुसार, आधी गुणाकार (3×4=12) मग बेरीज (2+12=14).",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
    {
        "text": "त्रिकोणाच्या तीन कोनांची बेरीज किती असते?",
        "type": QuestionType.MCQ,
        "options": {"a": "90°", "b": "180°", "c": "270°", "d": "360°"},
        "answer": "b",
        "explanation": "प्रत्येक त्रिकोणाच्या तीन अंतर्गत कोनांची बेरीज नेहमी 180° असते.",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
    {
        "text": "12 चा 25% किती?",
        "type": QuestionType.MCQ,
        "options": {"a": "2", "b": "3", "c": "4", "d": "6"},
        "answer": "b",
        "explanation": "12 × 25/100 = 12 × 0.25 = 3",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
    {
        "text": "x + 5 = 12 तर x = ?",
        "type": QuestionType.MCQ,
        "options": {"a": "5", "b": "6", "c": "7", "d": "17"},
        "answer": "c",
        "explanation": "x = 12 - 5 = 7",
        "marks": 1,
        "difficulty": DifficultyLevel.MEDIUM,
    },
    {
        "text": "वर्तुळाचे क्षेत्रफळ कसे काढतात?",
        "type": QuestionType.MCQ,
        "options": {"a": "πr", "b": "2πr", "c": "πr²", "d": "2πr²"},
        "answer": "c",
        "explanation": "वर्तुळाचे क्षेत्रफळ = πr², जेथे r = त्रिज्या.",
        "marks": 2,
        "difficulty": DifficultyLevel.MEDIUM,
    },
]

SCIENCE_QUESTIONS = [
    {
        "text": "प्रकाश संश्लेषणासाठी कोणता वायू आवश्यक आहे?",
        "type": QuestionType.MCQ,
        "options": {"a": "ऑक्सिजन", "b": "कार्बन डायऑक्साइड", "c": "नायट्रोजन", "d": "हायड्रोजन"},
        "answer": "b",
        "explanation": "वनस्पती प्रकाश संश्लेषणात कार्बन डायऑक्साइड (CO₂) शोषतात आणि ऑक्सिजन सोडतात.",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
    {
        "text": "पाण्याचे रासायनिक सूत्र काय आहे?",
        "type": QuestionType.MCQ,
        "options": {"a": "CO₂", "b": "H₂O", "c": "NaCl", "d": "O₂"},
        "answer": "b",
        "explanation": "पाण्याचे रासायनिक सूत्र H₂O आहे — 2 हायड्रोजन + 1 ऑक्सिजन.",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
    {
        "text": "मानवी शरीरातील सर्वात मोठा अवयव कोणता?",
        "type": QuestionType.MCQ,
        "options": {"a": "यकृत", "b": "हृदय", "c": "त्वचा", "d": "मेंदू"},
        "answer": "c",
        "explanation": "त्वचा हा मानवी शरीरातील सर्वात मोठा अवयव आहे.",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
    {
        "text": "प्रकाशाचा वेग किती आहे?",
        "type": QuestionType.MCQ,
        "options": {"a": "3 × 10⁶ m/s", "b": "3 × 10⁸ m/s", "c": "3 × 10¹⁰ m/s", "d": "3 × 10⁴ m/s"},
        "answer": "b",
        "explanation": "प्रकाशाचा वेग अंदाजे 3 × 10⁸ मीटर/सेकंद (≈ 3 लाख किमी/सेकंद) आहे.",
        "marks": 2,
        "difficulty": DifficultyLevel.MEDIUM,
    },
    {
        "text": "पृथ्वीचा एक परिभ्रमण किती दिवसांत होतो?",
        "type": QuestionType.TRUE_FALSE,
        "options": {"true": "365 दिवस", "false": "365 दिवस नाही"},
        "answer": "true",
        "explanation": "पृथ्वी सूर्याभोवती एक परिभ्रमण अंदाजे 365.25 दिवसांत पूर्ण करते.",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
]

MARATHI_QUESTIONS = [
    {
        "text": "'मराठी' भाषेतील 'वचन' म्हणजे काय?",
        "type": QuestionType.MCQ,
        "options": {"a": "एकवचन-अनेकवचन", "b": "लिंग", "c": "विभक्ती", "d": "काळ"},
        "answer": "a",
        "explanation": "वचन म्हणजे एकवचन (एक) आणि अनेकवचन (अनेक) यांचे बोधन.",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
    {
        "text": "'घोडा' या शब्दाचे अनेकवचन काय?",
        "type": QuestionType.MCQ,
        "options": {"a": "घोडे", "b": "घोडी", "c": "घोडा", "d": "घोड्या"},
        "answer": "a",
        "explanation": "'घोडा' चे अनेकवचन 'घोडे' आहे.",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
    {
        "text": "'सूर्य पूर्वेला उगवतो.' या वाक्यात क्रियापद कोणते?",
        "type": QuestionType.MCQ,
        "options": {"a": "सूर्य", "b": "पूर्वेला", "c": "उगवतो", "d": "या"},
        "answer": "c",
        "explanation": "'उगवतो' हे क्रियापद आहे — ते क्रिया दर्शवते.",
        "marks": 1,
        "difficulty": DifficultyLevel.EASY,
    },
]


async def seed():
    """Create sample assignments and tests."""
    async with async_session() as db:
        # Find student user
        student = await db.scalar(
            select(User).where(User.phone == "9999999001")
        )
        # Find teacher user (as creator)
        teacher = await db.scalar(
            select(User).where(User.phone == "9999999002")
        )
        if not teacher:
            logger.error("❌ Teacher user not found. Run seed_dev_users first.")
            return

        # Find subjects for grade 7
        subjects_result = await db.execute(
            select(Subject).where(Subject.grade == 7).order_by(Subject.display_order)
        )
        subjects = list(subjects_result.scalars().all())

        if not subjects:
            logger.warning("⚠️ No subjects found for grade 7. Run seed_syllabus first.")
            logger.info("   Creating assignments without subject linkage...")
            # Create placeholder to avoid crash
            subjects = []

        # Map subject names to objects
        subject_map = {}
        for s in subjects:
            if "गणित" in s.name or "math" in (s.name_en or "").lower():
                subject_map["math"] = s
            elif "विज्ञान" in s.name or "science" in (s.name_en or "").lower():
                subject_map["science"] = s
            elif "मराठी" in s.name and "सामाजिक" not in s.name:
                subject_map["marathi"] = s

        # Check if already seeded
        existing = await db.scalar(
            select(Assignment).where(Assignment.title == "गणित गृहपाठ १")
        )
        if existing:
            logger.info("⏭️  Assignments already seeded")
            return

        now = datetime.now(timezone.utc)
        created_count = 0

        # ── Homework Assignments ──────────────────────────────

        homework_data = [
            ("गणित गृहपाठ १", "BODMAS आणि मूलभूत गणित", "math", MATH_QUESTIONS[:3]),
            ("विज्ञान गृहपाठ १", "प्रकाश संश्लेषण आणि जीवशास्त्र", "science", SCIENCE_QUESTIONS[:3]),
            ("मराठी व्याकरण सराव", "वचन, लिंग आणि क्रियापद", "marathi", MARATHI_QUESTIONS),
        ]

        for title, desc, subj_key, questions_data in homework_data:
            subj = subject_map.get(subj_key)
            if not subj:
                logger.warning(f"  ⚠️ Subject '{subj_key}' not found, skipping {title}")
                continue

            assignment = Assignment(
                title=title,
                description=desc,
                assignment_type=AssignmentType.HOMEWORK,
                subject_id=subj.id,
                created_by=teacher.id,
                due_date=now + timedelta(days=7),
                max_score=sum(q["marks"] for q in questions_data),
                is_active=True,
            )
            db.add(assignment)
            await db.flush()

            for i, qd in enumerate(questions_data):
                question = Question(
                    assignment_id=assignment.id,
                    question_text=qd["text"],
                    question_type=qd["type"],
                    options=qd["options"],
                    correct_answer=qd["answer"],
                    explanation=qd["explanation"],
                    marks=qd["marks"],
                    difficulty=qd["difficulty"],
                    display_order=i + 1,
                )
                db.add(question)

            created_count += 1
            logger.info(f"  ✅ Homework: {title} ({len(questions_data)} questions)")

        # ── Tests ─────────────────────────────────────────────

        test_data = [
            ("गणित चाचणी १", "गणित — BODMAS, टक्केवारी, बीजगणित, क्षेत्रफळ", "math", MATH_QUESTIONS),
            ("विज्ञान चाचणी १", "विज्ञान — प्रकाश संश्लेषण, रसायन, शरीर, भौतिकशास्त्र", "science", SCIENCE_QUESTIONS),
        ]

        test_assignments = []
        for title, desc, subj_key, questions_data in test_data:
            subj = subject_map.get(subj_key)
            if not subj:
                continue

            assignment = Assignment(
                title=title,
                description=desc,
                assignment_type=AssignmentType.TEST,
                subject_id=subj.id,
                created_by=teacher.id,
                due_date=now + timedelta(days=14),
                max_score=sum(q["marks"] for q in questions_data),
                is_active=True,
            )
            db.add(assignment)
            await db.flush()

            question_ids = []
            for i, qd in enumerate(questions_data):
                question = Question(
                    assignment_id=assignment.id,
                    question_text=qd["text"],
                    question_type=qd["type"],
                    options=qd["options"],
                    correct_answer=qd["answer"],
                    explanation=qd["explanation"],
                    marks=qd["marks"],
                    difficulty=qd["difficulty"],
                    display_order=i + 1,
                )
                db.add(question)
                await db.flush()
                question_ids.append((str(question.id), qd["answer"]))

            test_assignments.append((assignment, question_ids))
            created_count += 1
            logger.info(f"  ✅ Test: {title} ({len(questions_data)} questions)")

        # ── Pre-submit one test for progress data ─────────────

        if student and test_assignments:
            test_assignment, q_ids = test_assignments[0]
            # Answer all correctly except the last one
            answers = {}
            for q_id, correct in q_ids[:-1]:
                answers[q_id] = correct
            # Wrong answer for last
            if q_ids:
                answers[q_ids[-1][0]] = "wrong"

            # Calculate score
            total = sum(q["marks"] for q in MATH_QUESTIONS)
            correct_marks = sum(q["marks"] for q in MATH_QUESTIONS[:-1])

            attempt = TestAttempt(
                student_id=student.id,
                assignment_id=test_assignment.id,
                answers=answers,
                score=correct_marks,
                max_score=total,
                percentage=round(correct_marks / total * 100, 1) if total > 0 else 0,
                submitted_at=now - timedelta(days=2),
                is_graded=True,
            )
            db.add(attempt)
            logger.info(f"  ✅ Pre-submitted test attempt: {correct_marks}/{total} marks")

        await db.commit()
        logger.info(f"\n🎉 Seeded {created_count} assignments/tests!")


def main():
    print("🌱 Seeding sample assignments and tests...\n")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
