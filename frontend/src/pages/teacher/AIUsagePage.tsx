/**
 * AIUsagePage — teacher's oversight of students' AI Guru conversations.
 */
import { useState, useEffect } from 'react';
import { Brain, TrendingUp, AlertTriangle, Users } from 'lucide-react';
import apiClient from '../../api/client';

interface AIUsageData {
  total_conversations: number;
  flagged_conversations: number;
  topics: { topic: string; count: number }[];
  most_active_students: { student_id: string; student_name: string; conversations: number }[];
  period_days: number;
}

export function AIUsagePage() {
  const [data, setData] = useState<AIUsageData | null>(null);
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [days]);

  async function loadData() {
    try {
      setLoading(true);
      const { data: result } = await apiClient.get(`/teachers/ai-usage?days=${days}`);
      setData(result);
    } catch { setData(null); } finally { setLoading(false); }
  }

  return (
    <div className="p-8 animate-fade-in" id="ai-usage-page">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold font-marathi flex items-center gap-3">
            <Brain size={24} className="text-pink-400" />
            AI वापर निरीक्षण
          </h1>
          <p className="text-white/40 mt-1 font-marathi text-sm">विद्यार्थी काय विचारत आहेत ते पहा</p>
        </div>

        {/* Period selector */}
        <div className="flex gap-2">
          {[7, 14, 30].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                days === d ? 'bg-brand-500/20 text-brand-300' : 'text-white/40 hover:bg-white/5'
              }`}
            >
              {d} दिवस
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card p-4 animate-pulse"><div className="h-12 bg-white/5 rounded" /></div>
          ))}
        </div>
      ) : data ? (
        <>
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="glass-card p-4 text-center bg-gradient-to-br from-purple-500/10 to-brand-500/5">
              <div className="text-2xl font-bold text-purple-400">{data.total_conversations}</div>
              <div className="text-[11px] text-white/40 font-marathi">एकूण AI संवाद</div>
            </div>
            <div className="glass-card p-4 text-center bg-gradient-to-br from-amber-500/10 to-orange-500/5">
              <div className="text-2xl font-bold text-amber-400">{data.flagged_conversations}</div>
              <div className="text-[11px] text-white/40 font-marathi flex items-center justify-center gap-1">
                <AlertTriangle size={10} /> सुरक्षा ध्वज
              </div>
            </div>
            <div className="glass-card p-4 text-center bg-gradient-to-br from-blue-500/10 to-cyan-500/5">
              <div className="text-2xl font-bold text-blue-400">{data.most_active_students.length}</div>
              <div className="text-[11px] text-white/40 font-marathi">सक्रिय विद्यार्थी</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top topics */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold font-marathi mb-4 flex items-center gap-2 text-white/70">
                <TrendingUp size={14} /> शीर्ष विषय
              </h3>
              {data.topics.length > 0 ? (
                <div className="space-y-2">
                  {data.topics.map((topic, i) => (
                    <div key={topic.topic} className="flex items-center justify-between p-2 rounded-lg hover:bg-white/[0.02]">
                      <span className="text-sm text-white/60 font-marathi">
                        <span className="text-white/20 mr-2">{i + 1}.</span>
                        {topic.topic}
                      </span>
                      <span className="text-xs text-brand-400">{topic.count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-white/20 text-center py-4 font-marathi">कोणताही विषय उपलब्ध नाही</p>
              )}
            </div>

            {/* Most active students */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold font-marathi mb-4 flex items-center gap-2 text-white/70">
                <Users size={14} /> सर्वात सक्रिय विद्यार्थी
              </h3>
              {data.most_active_students.length > 0 ? (
                <div className="space-y-2">
                  {data.most_active_students.map((student, i) => (
                    <div key={student.student_id} className="flex items-center justify-between p-2 rounded-lg hover:bg-white/[0.02]">
                      <span className="text-sm text-white/60 font-marathi">
                        <span className="text-white/20 mr-2">{i + 1}.</span>
                        {student.student_name}
                      </span>
                      <span className="text-xs text-emerald-400">{student.conversations} संवाद</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-white/20 text-center py-4 font-marathi">कोणताही विद्यार्थी सापडला नाही</p>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="glass-card p-12 text-center">
          <p className="text-white/30 font-marathi">डेटा उपलब्ध नाही</p>
        </div>
      )}
    </div>
  );
}
