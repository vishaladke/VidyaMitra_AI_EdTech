/**
 * ChildProgressPage — parent's view of a specific child's progress.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, BookOpen, MessageCircle, CheckCircle, BarChart3 } from 'lucide-react';
import apiClient from '../../api/client';

interface ChildProgress {
  child: { id: string; full_name: string; grade: number | null; streak_days: number };
  ai_stats: { total_conversations: number; total_messages: number; subjects: { name: string; conversations: number }[] };
  recent_tests: { score: number | null; max_score: number | null; percentage: number | null; submitted_at: string | null }[];
  attendance: { total_days: number; present_days: number; attendance_pct: number };
}

export function ChildProgressPage() {
  const { childId } = useParams<{ childId: string }>();
  const navigate = useNavigate();
  const [progress, setProgress] = useState<ChildProgress | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (childId) loadProgress(childId);
  }, [childId]);

  async function loadProgress(id: string) {
    try {
      setLoading(true);
      const { data } = await apiClient.get(`/parents/children/${id}`);
      setProgress(data);
    } catch { setProgress(null); } finally { setLoading(false); }
  }

  if (loading) {
    return (
      <div className="p-8 animate-fade-in">
        <div className="glass-card p-12 text-center">
          <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin mx-auto" />
        </div>
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="p-8 animate-fade-in">
        <button onClick={() => navigate('/parent')} className="flex items-center gap-2 text-white/50 hover:text-white mb-6">
          <ArrowLeft size={18} /> <span className="text-sm font-marathi">मागे</span>
        </button>
        <div className="glass-card p-12 text-center">
          <p className="text-white/30 font-marathi">मुलाची माहिती सापडली नाही</p>
        </div>
      </div>
    );
  }

  const c = progress.child;
  const ai = progress.ai_stats;
  const att = progress.attendance;

  return (
    <div className="p-8 animate-fade-in" id="child-progress-page">
      <button onClick={() => navigate('/parent')} className="flex items-center gap-2 text-white/50 hover:text-white mb-6 transition-colors">
        <ArrowLeft size={18} /> <span className="text-sm font-marathi">मागे</span>
      </button>

      {/* Child header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500/20 to-purple-600/20 flex items-center justify-center text-2xl">🎓</div>
        <div>
          <h1 className="text-xl font-bold font-marathi">{c.full_name}</h1>
          <p className="text-sm text-white/40">इयत्ता {c.grade} • स्ट्रीक: {c.streak_days} दिवस 🔥</p>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="glass-card p-4 text-center bg-gradient-to-br from-purple-500/10 to-brand-500/5">
          <MessageCircle size={18} className="text-purple-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-purple-400">{ai.total_conversations}</div>
          <div className="text-[10px] text-white/40 font-marathi">AI संवाद</div>
        </div>
        <div className="glass-card p-4 text-center bg-gradient-to-br from-blue-500/10 to-cyan-500/5">
          <BookOpen size={18} className="text-blue-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-blue-400">{ai.total_messages}</div>
          <div className="text-[10px] text-white/40 font-marathi">प्रश्न विचारले</div>
        </div>
        <div className="glass-card p-4 text-center bg-gradient-to-br from-emerald-500/10 to-green-500/5">
          <CheckCircle size={18} className="text-emerald-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-emerald-400">{att.attendance_pct}%</div>
          <div className="text-[10px] text-white/40 font-marathi">उपस्थिती (30 दिवस)</div>
        </div>
        <div className="glass-card p-4 text-center bg-gradient-to-br from-orange-500/10 to-red-500/5">
          <BarChart3 size={18} className="text-orange-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-orange-400">{ai.subjects.length}</div>
          <div className="text-[10px] text-white/40 font-marathi">विषय अभ्यासले</div>
        </div>
      </div>

      {/* Subjects */}
      {ai.subjects.length > 0 && (
        <div className="glass-card p-5 mb-6">
          <h3 className="text-sm font-semibold font-marathi mb-4 text-white/70">विषयनिहाय AI वापर</h3>
          <div className="space-y-3">
            {ai.subjects.map(sub => {
              const maxConv = Math.max(...ai.subjects.map(s => s.conversations));
              const pct = maxConv > 0 ? (sub.conversations / maxConv) * 100 : 0;
              return (
                <div key={sub.name}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-marathi text-white/60">{sub.name}</span>
                    <span className="text-xs text-brand-400">{sub.conversations}</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-brand-500 to-purple-500 rounded-full transition-all duration-700"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent tests */}
      {progress.recent_tests.length > 0 && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold font-marathi mb-4 text-white/70">अलीकडील चाचण्या</h3>
          <div className="space-y-2">
            {progress.recent_tests.map((test, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]">
                <span className="text-sm text-white/50 font-marathi">
                  चाचणी {i + 1}
                </span>
                <div className="flex items-center gap-3">
                  {test.percentage !== null && (
                    <span className={`text-sm font-bold ${test.percentage >= 75 ? 'text-emerald-400' : test.percentage >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                      {test.percentage}%
                    </span>
                  )}
                  {test.submitted_at && (
                    <span className="text-[10px] text-white/20">
                      {new Date(test.submitted_at).toLocaleDateString('mr-IN')}
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
