/**
 * ReportsPage — parent's view of weekly reports for all children.
 */
import { useState, useEffect } from 'react';
import { FileText, RefreshCw } from 'lucide-react';
import apiClient from '../../api/client';

interface WeeklyReport {
  student: { id: string; full_name: string; grade: number | null; streak_days: number };
  period: { start: string; end: string };
  ai_activity: { conversations: number; questions_asked: number; active_days: number; top_subjects: string[] };
  attendance: { total_days: number; present_days: number; percentage: number | null };
  tests: { completed: number; average_score: number | null };
  summary_mr: string;
}

export function ReportsPage() {
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadReports(); }, []);

  async function loadReports() {
    try {
      setLoading(true);
      const { data } = await apiClient.get('/parents/reports');
      setReports(data.reports || []);
    } catch { setReports([]); } finally { setLoading(false); }
  }

  return (
    <div className="p-8 animate-fade-in" id="reports-page">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold font-marathi flex items-center gap-3">
            <FileText size={24} className="text-purple-400" />
            साप्ताहिक अहवाल
          </h1>
          <p className="text-white/40 mt-1 font-marathi text-sm">तुमच्या मुलांचा साप्ताहिक अहवाल</p>
        </div>
        <button onClick={loadReports} disabled={loading}
          className="p-2.5 rounded-xl hover:bg-white/5 text-white/50 hover:text-white transition-all">
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map(i => (
            <div key={i} className="glass-card p-6 animate-pulse">
              <div className="h-6 bg-white/5 rounded w-1/3 mb-4" />
              <div className="h-32 bg-white/5 rounded" />
            </div>
          ))}
        </div>
      ) : reports.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <FileText size={36} className="text-white/10 mx-auto mb-4" />
          <p className="text-white/30 font-marathi">कोणताही अहवाल उपलब्ध नाही</p>
        </div>
      ) : (
        <div className="space-y-6">
          {reports.map(report => (
            <div key={report.student.id} className="glass-card overflow-hidden">
              {/* Header */}
              <div className="p-5 border-b border-white/5 bg-gradient-to-r from-brand-500/10 to-purple-600/5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🎓</span>
                    <div>
                      <h3 className="font-semibold font-marathi">{report.student.full_name}</h3>
                      <p className="text-[10px] text-white/30">
                        इयत्ता {report.student.grade} • {report.period.start} — {report.period.end}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-orange-400 flex items-center gap-1">
                    🔥 {report.student.streak_days} दिवस
                  </span>
                </div>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-4 gap-px bg-white/5">
                <div className="p-4 text-center bg-surface-950">
                  <div className="text-lg font-bold text-purple-400">{report.ai_activity.conversations}</div>
                  <div className="text-[9px] text-white/30 font-marathi">AI संवाद</div>
                </div>
                <div className="p-4 text-center bg-surface-950">
                  <div className="text-lg font-bold text-blue-400">{report.ai_activity.active_days}/7</div>
                  <div className="text-[9px] text-white/30 font-marathi">सक्रिय दिवस</div>
                </div>
                <div className="p-4 text-center bg-surface-950">
                  <div className="text-lg font-bold text-emerald-400">
                    {report.attendance.percentage !== null ? `${report.attendance.percentage}%` : '—'}
                  </div>
                  <div className="text-[9px] text-white/30 font-marathi">उपस्थिती</div>
                </div>
                <div className="p-4 text-center bg-surface-950">
                  <div className="text-lg font-bold text-amber-400">
                    {report.tests.average_score !== null ? `${report.tests.average_score}%` : '—'}
                  </div>
                  <div className="text-[9px] text-white/30 font-marathi">चाचणी सरासरी</div>
                </div>
              </div>

              {/* Marathi summary */}
              <div className="p-5 bg-white/[0.01]">
                <h4 className="text-[10px] text-white/20 mb-2 uppercase tracking-wider">WhatsApp अहवाल प्रत</h4>
                <pre className="text-sm text-white/50 font-marathi whitespace-pre-wrap leading-relaxed">
                  {report.summary_mr}
                </pre>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
