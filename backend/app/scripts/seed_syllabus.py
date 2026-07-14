"""Seed script — populate Maharashtra State Board syllabus for grades 5–10.

Run with: python -m app.scripts.seed_syllabus

Subjects: गणित (Math), विज्ञान (Science), मराठी, हिंदी, English, सामाजिक शास्त्र (Social Studies)
Board: maharashtra_state
Medium: Marathi

This creates subjects and a representative chapter/topic tree for each.
"""
import asyncio
import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Syllabus Data ─────────────────────────────────────────────

SUBJECTS = [
    {"name": "गणित", "name_en": "Mathematics", "display_order": 1},
    {"name": "विज्ञान", "name_en": "Science", "display_order": 2},
    {"name": "मराठी", "name_en": "Marathi", "display_order": 3},
    {"name": "हिंदी", "name_en": "Hindi", "display_order": 4},
    {"name": "English", "name_en": "English", "display_order": 5},
    {"name": "सामाजिक शास्त्र", "name_en": "Social Studies", "display_order": 6},
]

# Representative chapters per subject (grade 7 as example — can be expanded)
SYLLABUS_TREE = {
    "गणित": [
        {
            "title": "पूर्णांक", "title_en": "Integers", "order": 1,
            "topics": [
                {"title": "पूर्णांकांची गुणधर्म", "title_en": "Properties of Integers", "order": 1},
                {"title": "पूर्णांकांवरील क्रिया", "title_en": "Operations on Integers", "order": 2},
            ],
        },
        {
            "title": "भिन्न आणि दशांश", "title_en": "Fractions and Decimals", "order": 2,
            "topics": [
                {"title": "भिन्नांची तुलना", "title_en": "Comparing Fractions", "order": 1},
                {"title": "दशांश क्रिया", "title_en": "Decimal Operations", "order": 2},
            ],
        },
        {
            "title": "बीजगणित", "title_en": "Algebra", "order": 3,
            "topics": [
                {"title": "चल आणि व्यंजक", "title_en": "Variables and Expressions", "order": 1},
                {"title": "सरल समीकरणे", "title_en": "Simple Equations", "order": 2},
                {"title": "एकघाती समीकरणे", "title_en": "Linear Equations", "order": 3},
            ],
        },
        {
            "title": "भूमिती", "title_en": "Geometry", "order": 4,
            "topics": [
                {"title": "रेषा आणि कोन", "title_en": "Lines and Angles", "order": 1},
                {"title": "त्रिकोण", "title_en": "Triangles", "order": 2},
                {"title": "चतुर्भुज", "title_en": "Quadrilaterals", "order": 3},
            ],
        },
        {
            "title": "क्षेत्रफळ आणि परिमिती", "title_en": "Area and Perimeter", "order": 5,
            "topics": [
                {"title": "आयताचे क्षेत्रफळ", "title_en": "Area of Rectangle", "order": 1},
                {"title": "वर्तुळाचे क्षेत्रफळ", "title_en": "Area of Circle", "order": 2},
            ],
        },
    ],
    "विज्ञान": [
        {
            "title": "पोषण", "title_en": "Nutrition", "order": 1,
            "topics": [
                {"title": "वनस्पतींचे पोषण", "title_en": "Nutrition in Plants", "order": 1},
                {"title": "प्राण्यांचे पोषण", "title_en": "Nutrition in Animals", "order": 2},
                {"title": "प्रकाश संश्लेषण", "title_en": "Photosynthesis", "order": 3},
            ],
        },
        {
            "title": "उष्णता आणि तापमान", "title_en": "Heat and Temperature", "order": 2,
            "topics": [
                {"title": "उष्णता वाहन", "title_en": "Heat Transfer", "order": 1},
                {"title": "तापमान मापन", "title_en": "Measuring Temperature", "order": 2},
            ],
        },
        {
            "title": "आम्ल, आम्लारी आणि क्षार", "title_en": "Acids, Bases, and Salts", "order": 3,
            "topics": [
                {"title": "आम्लाचे गुणधर्म", "title_en": "Properties of Acids", "order": 1},
                {"title": "आम्लारी आणि क्षार", "title_en": "Bases and Salts", "order": 2},
            ],
        },
        {
            "title": "प्रकाश", "title_en": "Light", "order": 4,
            "topics": [
                {"title": "प्रकाशाचे परावर्तन", "title_en": "Reflection of Light", "order": 1},
                {"title": "लेन्स", "title_en": "Lenses", "order": 2},
            ],
        },
    ],
    "मराठी": [
        {
            "title": "गद्य विभाग", "title_en": "Prose Section", "order": 1,
            "topics": [
                {"title": "कथा वाचन", "title_en": "Story Reading", "order": 1},
                {"title": "निबंध लेखन", "title_en": "Essay Writing", "order": 2},
                {"title": "पत्र लेखन", "title_en": "Letter Writing", "order": 3},
            ],
        },
        {
            "title": "पद्य विभाग", "title_en": "Poetry Section", "order": 2,
            "topics": [
                {"title": "कविता अभ्यास", "title_en": "Poetry Study", "order": 1},
                {"title": "कवितेचा अर्थ", "title_en": "Poem Interpretation", "order": 2},
            ],
        },
        {
            "title": "व्याकरण", "title_en": "Grammar", "order": 3,
            "topics": [
                {"title": "नाम, सर्वनाम", "title_en": "Nouns, Pronouns", "order": 1},
                {"title": "क्रियापद", "title_en": "Verbs", "order": 2},
                {"title": "विभक्ती", "title_en": "Cases (Vibhakti)", "order": 3},
                {"title": "वाक्य रचना", "title_en": "Sentence Structure", "order": 4},
            ],
        },
    ],
    "हिंदी": [
        {
            "title": "गद्य खंड", "title_en": "Prose", "order": 1,
            "topics": [
                {"title": "कहानी पठन", "title_en": "Story Reading", "order": 1},
                {"title": "अनुच्छेद लेखन", "title_en": "Paragraph Writing", "order": 2},
            ],
        },
        {
            "title": "पद्य खंड", "title_en": "Poetry", "order": 2,
            "topics": [
                {"title": "कविता", "title_en": "Poems", "order": 1},
            ],
        },
        {
            "title": "व्याकरण", "title_en": "Grammar", "order": 3,
            "topics": [
                {"title": "संज्ञा, सर्वनाम", "title_en": "Nouns, Pronouns", "order": 1},
                {"title": "क्रिया", "title_en": "Verbs", "order": 2},
                {"title": "वाक्य रचना", "title_en": "Sentence Formation", "order": 3},
            ],
        },
    ],
    "English": [
        {
            "title": "Prose", "title_en": "Prose", "order": 1,
            "topics": [
                {"title": "Comprehension", "title_en": "Reading Comprehension", "order": 1},
                {"title": "Short Stories", "title_en": "Short Stories", "order": 2},
            ],
        },
        {
            "title": "Poetry", "title_en": "Poetry", "order": 2,
            "topics": [
                {"title": "Poem Analysis", "title_en": "Poem Analysis", "order": 1},
            ],
        },
        {
            "title": "Grammar", "title_en": "Grammar", "order": 3,
            "topics": [
                {"title": "Tenses", "title_en": "Tenses", "order": 1},
                {"title": "Parts of Speech", "title_en": "Parts of Speech", "order": 2},
                {"title": "Active and Passive Voice", "title_en": "Active and Passive Voice", "order": 3},
                {"title": "Direct and Indirect Speech", "title_en": "Direct and Indirect Speech", "order": 4},
            ],
        },
        {
            "title": "Writing", "title_en": "Writing", "order": 4,
            "topics": [
                {"title": "Essay Writing", "title_en": "Essay Writing", "order": 1},
                {"title": "Letter Writing", "title_en": "Letter Writing", "order": 2},
            ],
        },
    ],
    "सामाजिक शास्त्र": [
        {
            "title": "इतिहास", "title_en": "History", "order": 1,
            "topics": [
                {"title": "मध्ययुगीन भारत", "title_en": "Medieval India", "order": 1},
                {"title": "मुघल साम्राज्य", "title_en": "Mughal Empire", "order": 2},
                {"title": "मराठा साम्राज्य", "title_en": "Maratha Empire", "order": 3},
            ],
        },
        {
            "title": "भूगोल", "title_en": "Geography", "order": 2,
            "topics": [
                {"title": "भारताचा भूगोल", "title_en": "Geography of India", "order": 1},
                {"title": "महाराष्ट्राचा भूगोल", "title_en": "Geography of Maharashtra", "order": 2},
                {"title": "हवामान", "title_en": "Climate", "order": 3},
            ],
        },
        {
            "title": "नागरिकशास्त्र", "title_en": "Civics", "order": 3,
            "topics": [
                {"title": "लोकशाही", "title_en": "Democracy", "order": 1},
                {"title": "भारतीय संविधान", "title_en": "Indian Constitution", "order": 2},
            ],
        },
    ],
}


async def seed_syllabus():
    """Seed subjects and syllabus units for grades 5–10."""
    from app.database import async_session_factory
    from app.models.syllabus import Subject, SyllabusUnit

    async with async_session_factory() as db:
        created_subjects = 0
        created_units = 0

        for grade in range(5, 11):  # Grades 5–10
            for subj_data in SUBJECTS:
                # Check if subject already exists
                result = await db.execute(
                    select(Subject).where(
                        Subject.name == subj_data["name"],
                        Subject.grade == grade,
                        Subject.board == "maharashtra_state",
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    logger.info(f"  Subject exists: {subj_data['name']} (Grade {grade}) — skipping")
                    subject_id = existing.id
                else:
                    subject = Subject(
                        id=uuid.uuid4(),
                        name=subj_data["name"],
                        name_en=subj_data["name_en"],
                        grade=grade,
                        board="maharashtra_state",
                        display_order=subj_data["display_order"],
                        is_active=True,
                    )
                    db.add(subject)
                    subject_id = subject.id
                    created_subjects += 1
                    logger.info(f"  ✅ Created subject: {subj_data['name']} (Grade {grade})")

                # Seed chapters and topics from the tree
                tree = SYLLABUS_TREE.get(subj_data["name"], [])
                for chapter_data in tree:
                    # Check if chapter exists
                    result = await db.execute(
                        select(SyllabusUnit).where(
                            SyllabusUnit.subject_id == subject_id,
                            SyllabusUnit.title == chapter_data["title"],
                            SyllabusUnit.unit_type == "chapter",
                        )
                    )
                    existing_chapter = result.scalar_one_or_none()

                    if existing_chapter:
                        chapter_id = existing_chapter.id
                    else:
                        chapter = SyllabusUnit(
                            id=uuid.uuid4(),
                            subject_id=subject_id,
                            parent_id=None,
                            title=chapter_data["title"],
                            title_en=chapter_data.get("title_en"),
                            unit_type="chapter",
                            display_order=chapter_data["order"],
                            version=1,
                            is_active=True,
                        )
                        db.add(chapter)
                        chapter_id = chapter.id
                        created_units += 1

                    # Seed topics under this chapter
                    for topic_data in chapter_data.get("topics", []):
                        result = await db.execute(
                            select(SyllabusUnit).where(
                                SyllabusUnit.subject_id == subject_id,
                                SyllabusUnit.parent_id == chapter_id,
                                SyllabusUnit.title == topic_data["title"],
                            )
                        )
                        existing_topic = result.scalar_one_or_none()

                        if not existing_topic:
                            topic = SyllabusUnit(
                                id=uuid.uuid4(),
                                subject_id=subject_id,
                                parent_id=chapter_id,
                                title=topic_data["title"],
                                title_en=topic_data.get("title_en"),
                                unit_type="topic",
                                display_order=topic_data["order"],
                                version=1,
                                is_active=True,
                            )
                            db.add(topic)
                            created_units += 1

        await db.commit()

    logger.info(f"\n🎓 Syllabus seeded: {created_subjects} subjects, {created_units} units across grades 5–10")


if __name__ == "__main__":
    asyncio.run(seed_syllabus())
