/**
 * ProgressPage — Student progress dashboard with per-subject stats.
 *
 * Features:
 * - Overall stats row: streak, conversations, subjects, completion
 * - Per-subject progress cards with circular progress ring
 * - Activity heatmap (last 30 days)
 * - Achievement badges for streak milestones
 */
import { useState, useEffect } from 'react';
import {
  BarChart3, Flame, MessageCircle, BookOpen,
  Target, TrendingUp, Award, Calendar,
} from 'lucide-react';
import apiClient from '../../api/client';

interface SubjectProgress {
  subject_id: string;
  subject_name: string;
  subject_name_en?: string;
  total_units: number;
  units_studied: number;
  completion_pct: number;
  conversation_count: number;
  last_studied?: string;
}

interface ProgressData {
  streak_days: number;
  total_conversations: number;
  total_messages: number;
  subjects_started: number;
  total_subjects: number;
  overall_completion_pct: number;
  assignments_completed: number;
  tests_completed: number;
  average_test_score?: number;
  subjects: SubjectProgress[];
  recent_activity: { date: string; count: number }[];
}

const STREAK_BADGES = [
  { days: 3, label: '3 दिवस', emoji: '🔥', color: 'from-orange-500/20 to-red-500/10' },
  { days: 7, label: '1 आठवडा', emoji: '⭐', color: 'from-amber-500/20 to-yellow-500/10' },
  { days: 14, label: '2 आठवडे', emoji: '🏆', color: 'from-yellow-500/20 to-amber-500/10' },
  { days: 30, label: '1 महिना', emoji: '💎', color: 'from-blue-500/20 to-cyan-500/10' },
  { days: 60, label: '2 महिने', emoji: '🚀', color: 'from-purple-500/20 to-pink-500/10' },
  { days: 100, label: '100 दिवस', emoji: '👑', color: 'from-emerald-500/20 to-green-500/10' },
];

const SUBJECT_COLORS = [
  { bg: 'from-blue-500/15 to-blue-600/5', ring: '#3b82f6', text: 'text-blue-400' },
  { bg: 'from-emerald-500/15 to-emerald-600/5', ring: '#10b981', text: 'text-emerald-400' },
  { bg: 'from-purple-500/15 to-purple-600/5', ring: '#8b5cf6', text: 'text-purple-400' },
  { bg: 'from-amber-500/15 to-amber-600/5', ring: '#f59e0b', text: 'text-amber-400' },
  { bg: 'from-rose-500/15 to-rose-600/5', ring: '#f43f5e', text: 'text-rose-400' },
  { bg: 'from-cyan-500/15 to-cyan-600/5', ring: '#06b6d4', text: 'text-cyan-400' },
];

export function ProgressPage() {
  const [data, setData] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadProgress(); }, []);

  async function loadProgress() {
    try {
      setLoading(true);
      const { data: resp } = await apiClient.get('/students/progress');
      setData(resp);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="h-8 bg-white/5 rounded w-48 mb-8 animate-pulse" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="glass-card p-5 animate-pulse">
              <div className="h-10 bg-white/5 rounded mb-3" />
              <div className="h-4 bg-white/5 rounded w-2/3" />
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card p-6 animate-pulse">
              <div className="h-24 bg-white/5 rounded mb-3" />
              <div className="h-4 bg-white/5 rounded w-3/4" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 text-center py-16">
        <BarChart3 size={48} className="text-white/10 mx-auto mb-4" />
        <p className="text-white/30 font-marathi">प्रगती डेटा लोड करता आला नाही</p>
      </div>
    );
  }

  // Build 30-day activity map
  const activityMap = new Map<string, number>();
  data.recent_activity.forEach(a => {
    if (a.date) {
      const dateStr = a.date.split('T')[0];
      activityMap.set(dateStr, a.count);
    }
  });

  const today = new Date();
  const last30Days: { date: string; count: number; label: string }[] = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().split('T')[0];
    last30Days.push({
      date: key,
      count: activityMap.get(key) || 0,
      label: d.toLocaleDateString('mr-IN', { day: 'numeric', month: 'short' }),
    });
  }

  const earnedBadges = STREAK_BADGES.filter(b => data.streak_days >= b.days);

  return (
    <div className="p-8 animate-fade-in" id="progress-page">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold font-marathi flex items-center gap-3">
          <BarChart3 size={24} className="text-pink-400" />
          माझी प्रगती
        </h1>
        <p className="text-white/40 mt-1 font-marathi text-sm">तुमची अभ्यास प्रगती आणि आकडेवारी</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Flame size={20} />}
          label="स्ट्रीक"
          value={`${data.streak_days} दिवस`}
          gradient="from-orange-500/20 to-red-500/10"
          iconColor="text-orange-400"
        />
        <StatCard
          icon={<MessageCircle size={20} />}
          label="AI संवाद"
          value={`${data.total_conversations}`}
          gradient="from-purple-500/20 to-brand-500/10"
          iconColor="text-purple-400"
        />
        <StatCard
          icon={<Target size={20} />}
          label="एकूण पूर्णता"
          value={`${data.overall_completion_pct}%`}
          gradient="from-emerald-500/20 to-green-500/10"
          iconColor="text-emerald-400"
        />
        <StatCard
          icon={<Award size={20} />}
          label="सरासरी गुण"
          value={data.average_test_score !== null && data.average_test_score !== undefined ? `${data.average_test_score}%` : '—'}
          gradient="from-amber-500/20 to-yellow-500/10"
          iconColor="text-amber-400"
        />
      </div>

      {/* Quick stats pills */}
      <div className="flex flex-wrap gap-3 mb-8">
        <span className="px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/5 text-sm text-white/50">
          📝 {data.assignments_completed} असाइनमेंट पूर्ण
        </span>
        <span className="px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/5 text-sm text-white/50">
          📋 {data.tests_completed} चाचण्या पूर्ण
        </span>
        <span className="px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/5 text-sm text-white/50">
          💬 {data.total_messages} प्रश्न विचारले
        </span>
        <span className="px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/5 text-sm text-white/50">
          📚 {data.subjects_started}/{data.total_subjects} विषय सुरू
        </span>
      </div>

      {/* Subject Progress Cards */}
      <h2 className="text-lg font-semibold font-marathi mb-4 flex items-center gap-2 text-white/80">
        <BookOpen size={18} />
        विषयनिहाय प्रगती
      </h2>

      {data.subjects.length === 0 ? (
        <div className="glass-card p-8 text-center mb-8">
          <BookOpen size={32} className="text-white/10 mx-auto mb-3" />
          <p className="text-white/30 font-marathi text-sm">अभ्यासक्रम डेटा अजून उपलब्ध नाही</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {data.subjects.map((subj, i) => {
            const colors = SUBJECT_COLORS[i % SUBJECT_COLORS.length];
            return (
              <div key={subj.subject_id} className={`glass-card p-5 bg-gradient-to-br ${colors.bg}`}>
                <div className="flex items-start gap-4">
                  {/* Progress ring */}
                  <div className="relative flex-shrink-0">
                    <svg width="64" height="64" viewBox="0 0 64 64" className="progress-ring">
                      <circle
                        cx="32" cy="32" r="28"
                        fill="none"
                        stroke="rgba(255,255,255,0.05)"
                        strokeWidth="4"
                      />
                      <circle
                        cx="32" cy="32" r="28"
                        fill="none"
                        stroke={colors.ring}
                        strokeWidth="4"
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 28}`}
                        strokeDashoffset={`${2 * Math.PI * 28 * (1 - subj.completion_pct / 100)}`}
                      />
                    </svg>
                    <span className={`absolute inset-0 flex items-center justify-center text-sm font-bold ${colors.text}`}>
                      {subj.completion_pct}%
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold font-marathi text-white/90 truncate">{subj.subject_name}</h3>
                    {subj.subject_name_en && (
                      <p className="text-[10px] text-white/30">{subj.subject_name_en}</p>
                    )}
                    <div className="mt-2 space-y-1">
                      <p className="text-xs text-white/40">
                        {subj.units_studied}/{subj.total_units} अध्याय पूर्ण
                      </p>
                      <p className="text-xs text-white/30">
                        {subj.conversation_count} AI संवाद
                      </p>
                      {subj.last_studied && (
                        <p className="text-[10px] text-white/20">
                          शेवटचा अभ्यास: {new Date(subj.last_studied).toLocaleDateString('mr-IN')}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Activity Heatmap */}
      <h2 className="text-lg font-semibold font-marathi mb-4 flex items-center gap-2 text-white/80">
        <Calendar size={18} />
        गेल्या 30 दिवसांची क्रिया
      </h2>

      <div className="glass-card p-5 mb-8">
        <div className="flex gap-1 flex-wrap">
          {last30Days.map(day => {
            const intensity = day.count === 0 ? 0 : Math.min(day.count, 5);
            const bgClass = intensity === 0
              ? 'bg-white/[0.03]'
              : intensity === 1
              ? 'bg-emerald-500/20'
              : intensity === 2
              ? 'bg-emerald-500/30'
              : intensity === 3
              ? 'bg-emerald-500/50'
              : intensity === 4
              ? 'bg-emerald-500/70'
              : 'bg-emerald-500';

            return (
              <div key={day.date} className="group relative">
                <div className={`w-7 h-7 md:w-8 md:h-8 rounded-md ${bgClass} transition-all hover:ring-2 hover:ring-white/20`} />
                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded bg-surface-800 text-[10px] text-white/70 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                  {day.label}: {day.count} संवाद
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex items-center gap-2 mt-3 text-[10px] text-white/30">
          <span>कमी</span>
          <div className="flex gap-0.5">
            {['bg-white/[0.03]', 'bg-emerald-500/20', 'bg-emerald-500/30', 'bg-emerald-500/50', 'bg-emerald-500/70', 'bg-emerald-500'].map(c => (
              <div key={c} className={`w-3 h-3 rounded-sm ${c}`} />
            ))}
          </div>
          <span>जास्त</span>
        </div>
      </div>

      {/* Streak Achievements */}
      <h2 className="text-lg font-semibold font-marathi mb-4 flex items-center gap-2 text-white/80">
        <Award size={18} />
        उपलब्धी
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {STREAK_BADGES.map(badge => {
          const earned = data.streak_days >= badge.days;
          return (
            <div
              key={badge.days}
              className={`glass-card p-4 text-center transition-all ${
                earned
                  ? `bg-gradient-to-br ${badge.color}`
                  : 'opacity-30 grayscale'
              }`}
            >
              <div className="text-2xl mb-2">{badge.emoji}</div>
              <p className="text-xs font-marathi text-white/70">{badge.label}</p>
              <p className="text-[10px] text-white/30 mt-1">
                {earned ? '✅ मिळवले!' : `${badge.days - data.streak_days} दिवस बाकी`}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Helper Components ──────────────────────────────────────

function StatCard({ icon, label, value, gradient, iconColor }: {
  icon: React.ReactNode;
  label: string;
  value: string;
  gradient: string;
  iconColor: string;
}) {
  return (
    <div className={`glass-card p-4 bg-gradient-to-br ${gradient}`}>
      <div className={`${iconColor} mb-2`}>{icon}</div>
      <div className="text-lg font-bold font-marathi">{value}</div>
      <div className="text-[11px] text-white/40 font-marathi">{label}</div>
    </div>
  );
}
