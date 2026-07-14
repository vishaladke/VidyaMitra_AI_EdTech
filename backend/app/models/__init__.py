# Models package — import all models so Alembic sees them
from app.models.user import User, StudentProfile, TeacherProfile, ParentProfile, ParentStudentLink  # noqa: F401
from app.models.school import School, Class, Section, TeacherClassAssignment  # noqa: F401
from app.models.syllabus import Subject, SyllabusUnit  # noqa: F401
from app.models.assessment import Assignment, Question, TestAttempt  # noqa: F401
from app.models.ai import AIConversation, AIMessage, AICostLog, AISemanticCache, FAQBank  # noqa: F401
from app.models.attendance import AttendanceRecord  # noqa: F401
from app.models.payment import Subscription, Payment  # noqa: F401
from app.models.notification import NotificationLog  # noqa: F401
from app.models.content import HomepageContent, AdSlot, AuditLog  # noqa: F401
