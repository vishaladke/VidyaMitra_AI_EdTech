/**
 * StudentProgressPage — teacher's view of student roster + per-student drill-down.
 */
import { useState, useEffect } from 'react';
import { ArrowLeft, BarChart3, MessageCircle, Flame, BookOpen } from 'lucide-react';
import apiClient from '../../api/client';

interface Student {
  id: string;
  full_name: string;
  grade: number | null;
  streak_days: number;
}

interface StudentDetail {
  student: { id: string; full_name: string; grade: number | null; streak_days: number };
  ai_stats: { total_conversations: number; total_messages: number; subjects: { name: string; conversation_count: number }[] };
  recent_conversations: { id: string; title: string; is_flagged: boolean; created_at: string | null }[];
  recent_tests: { score: number | null; max_score: number | null; percentage: number | null }[];
}

export function StudentProgressPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [selected, setSelected] = useState<StudentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadStudents(); }, []);

  async function loadStudents() {
    try {
      setLoading(true);
      const { data } = await apiClient.get('/teachers/students');
      setStudents(data.students || []);
    } catch { setStudents([]); } finally { setLoading(false); }
  }

  async function selectStudent(id: string) {
    try {
      const { data } = await apiClient.get(`/teachers/students/${id}`);
      setSelected(data);
    } catch { /* fallback */ }
  }

  if (selected) {
    const s = selected.student;
    const ai = selected.ai_stats;
    return (
      <div className="p-8 animate-fade-in" id="student-detail">
        <button onClick={() => setSelected(null)} className="flex items-center gap-2 text-white/50 hover:text-white mb-6 transition-colors">
          <ArrowLeft size={18} /> <span className="text-sm font-marathi">मागे</span>
        </button>

        <div className="flex items-center gap-4 mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500/20 to-purple-600/20 flex items-center justify-center text-2xl">🎓</div>
          <div>
            <h1 className="text-xl font-bold font-marathi">{s.full_name}</h1>
            <p className="text-sm text-white/40">इयत्ता {s.grade} • स्ट्रीक: {s.streak_days} दिवस 🔥</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="glass-card p-4 text-center bg-gradient-to-br from-purple-500/10 to-brand-500/5">
            <div className="text-lg font-bold text-purple-400">{ai.total_conversations}</div>
            <div className="text-[10px] text-white/40 font-marathi">AI संवाद</div>
          </div>
          <div className="glass-card p-4 text-center bg-gradient-to-br from-blue-500/10 to-cyan-500/5">
            <div className="text-lg font-bold text-blue-400">{ai.total_messages}</div>
            <div className="text-[10px] text-white/40 font-marathi">प्रश्न विचारले</div>
          </div>
          <div className="glass-card p-4 text-center bg-gradient-to-br from-orange-500/10 to-red-500/5">
            <div className="text-lg font-bold text-orange-400">{ai.subjects.length}</div>
            <div className="text-[10px] text-white/40 font-marathi">विषय</div>
          </div>
        </div>

        {/* Subject distribution */}
        {ai.subjects.length > 0 && (
          <div className="mb-8">
            <h3 className="text-sm font-semibold font-marathi mb-3 text-white/60 flex items-center gap-2">
              <BookOpen size={14} /> विषयनिहाय AI वापर
            </h3>
            <div className="space-y-2">
              {ai.subjects.map(sub => (
                <div key={sub.name} className="glass-card p-3 flex items-center justify-between">
                  <span className="text-sm font-marathi text-white/70">{sub.name}</span>
                  <span className="text-xs text-brand-400">{sub.conversation_count} संवाद</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent conversations */}
        {selected.recent_conversations.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold font-marathi mb-3 text-white/60 flex items-center gap-2">
              <MessageCircle size={14} /> अलीकडील AI संवाद
            </h3>
            <div className="space-y-2">
              {selected.recent_conversations.map(conv => (
                <div key={conv.id} className={`glass-card p-3 ${conv.is_flagged ? 'border-amber-500/30 border' : ''}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-marathi text-white/70">
                      {conv.is_flagged && '⚠️ '}{conv.title}
                    </span>
                    {conv.created_at && (
                      <span className="text-[10px] text-white/20">
                        {new Date(conv.created_at).toLocaleDateString('mr-IN')}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-8 animate-fade-in" id="student-progress-page">
      <div className="mb-8">
        <h1 className="text-2xl font-bold font-marathi flex items-center gap-3">
          <BarChart3 size={24} className="text-purple-400" />
          विद्यार्थी प्रगती
        </h1>
        <p className="text-white/40 mt-1 font-marathi text-sm">विद्यार्थ्यांचे सामर्थ्य आणि कमकुवतपणा पहा</p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card p-4 animate-pulse"><div className="h-5 bg-white/5 rounded w-1/3" /></div>
          ))}
        </div>
      ) : students.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <p className="text-white/30 font-marathi">कोणतेही विद्यार्थी सापडले नाहीत</p>
        </div>
      ) : (
        <div className="space-y-2">
          {students.map(student => (
            <button
              key={student.id}
              onClick={() => selectStudent(student.id)}
              className="glass-card w-full p-4 flex items-center justify-between hover:bg-white/[0.03] hover:border-white/15 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500/20 to-purple-600/10 flex items-center justify-center text-lg">🎓</div>
                <div className="text-left">
                  <span className="text-sm font-marathi text-white/80 group-hover:text-white">{student.full_name}</span>
                  <span className="text-[10px] text-white/20 block">इयत्ता {student.grade}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-orange-400 flex items-center gap-1">
                  <Flame size={12} /> {student.streak_days}
                </span>
                <span className="text-[10px] text-white/20">→</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
