/**
 * Student Dashboard — functional dashboard with real widgets.
 *
 * Features:
 * - Today's progress summary
 * - Quick-access subject cards
 * - "Ask AI Guru" floating action button
 * - Active streak display
 * - Recent conversations list
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen, MessageCircle, ClipboardList, BarChart3, Sparkles,
  Flame, Zap, TrendingUp, Clock,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import apiClient from '../../api/client';

interface DashboardStats {
  total_subjects: number;
  subjects_started: number;
  total_conversations: number;
  total_messages: number;
  streak_days: number;
  last_active: string | null;
}

interface RecentConversation {
  id: string;
  title: string;
  subject_id: string | null;
  created_at: string | null;
}

export function StudentDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentConvos, setRecentConvos] = useState<RecentConversation[]>([]);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      const { data } = await apiClient.get('/students/dashboard');
      if (data.stats) setStats(data.stats);
      if (data.recent_conversations) setRecentConvos(data.recent_conversations);
    } catch {
      // Use defaults — dashboard works even without API
    }
  }

  const greeting = getGreeting();
  const streakDays = stats?.streak_days || 0;

  return (
    <div className="p-8 animate-fade-in relative" id="student-dashboard">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold font-marathi">
          {greeting}, {user?.full_name || 'विद्यार्थी'} 🎓
        </h1>
        <p className="text-white/40 mt-1 font-marathi text-sm">
          आज काय शिकायचे आहे?
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Flame size={20} />}
          label="स्ट्रीक"
          value={`${streakDays} दिवस`}
          gradient="from-orange-500/20 to-red-500/10"
          iconColor="text-orange-400"
        />
        <StatCard
          icon={<MessageCircle size={20} />}
          label="AI संवाद"
          value={`${stats?.total_conversations || 0}`}
          gradient="from-purple-500/20 to-brand-500/10"
          iconColor="text-purple-400"
        />
        <StatCard
          icon={<BookOpen size={20} />}
          label="विषय सुरू"
          value={`${stats?.subjects_started || 0}/${stats?.total_subjects || 6}`}
          gradient="from-blue-500/20 to-cyan-500/10"
          iconColor="text-blue-400"
        />
        <StatCard
          icon={<Zap size={20} />}
          label="प्रश्न विचारले"
          value={`${stats?.total_messages || 0}`}
          gradient="from-emerald-500/20 to-green-500/10"
          iconColor="text-emerald-400"
        />
      </div>

      {/* Main modules grid */}
      <h2 className="text-lg font-semibold font-marathi mb-4 flex items-center gap-2 text-white/80">
        <TrendingUp size={18} />
        तुमचे मॉड्यूल
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
        <ModuleCard
          icon={<BookOpen size={28} />}
          title="अभ्यासक्रम"
          desc="विषय → अध्याय → विषय ब्राउझ करा"
          gradient="from-blue-500/20 to-blue-600/10"
          onClick={() => navigate('/student/syllabus')}
        />
        <ModuleCard
          icon={<Sparkles size={28} />}
          title="AI गुरू"
          desc="मराठीत AI ट्यूटर — तुमच्या प्रश्नांची उत्तरे"
          gradient="from-purple-500/20 to-purple-600/10"
          onClick={() => navigate('/student/ai-guru')}
          badge="✨ नवीन"
        />
        <ModuleCard
          icon={<ClipboardList size={28} />}
          title="असाइनमेंट"
          desc="गृहपाठ आणि सराव"
          gradient="from-green-500/20 to-green-600/10"
          comingSoon
        />
        <ModuleCard
          icon={<BarChart3 size={28} />}
          title="चाचण्या"
          desc="ऑटो-ग्रेडिंगसह चाचण्या"
          gradient="from-yellow-500/20 to-yellow-600/10"
          comingSoon
        />
        <ModuleCard
          icon={<BarChart3 size={28} />}
          title="प्रगती"
          desc="तुमची पूर्णता % आणि स्ट्रीक"
          gradient="from-pink-500/20 to-pink-600/10"
          comingSoon
        />
      </div>

      {/* Recent conversations */}
      {recentConvos.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold font-marathi mb-4 flex items-center gap-2 text-white/80">
            <Clock size={18} />
            अलीकडील संवाद
          </h2>
          <div className="space-y-2">
            {recentConvos.map(conv => (
              <button
                key={conv.id}
                onClick={() => navigate('/student/ai-guru')}
                className="glass-card w-full p-4 text-left hover:bg-white/[0.03] hover:border-white/15 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center">
                      <MessageCircle size={14} className="text-brand-400" />
                    </div>
                    <span className="text-sm font-marathi text-white/70 group-hover:text-white transition-colors">
                      {conv.title}
                    </span>
                  </div>
                  {conv.created_at && (
                    <span className="text-[10px] text-white/20">
                      {new Date(conv.created_at).toLocaleDateString('mr-IN')}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Floating AI Guru button */}
      <button
        onClick={() => navigate('/student/ai-guru')}
        className="fixed bottom-8 right-8 w-14 h-14 rounded-2xl
                   bg-gradient-to-br from-brand-500 to-purple-600
                   flex items-center justify-center shadow-2xl shadow-brand-500/30
                   hover:scale-110 hover:shadow-brand-500/50
                   active:scale-95 transition-all duration-300 z-50"
        id="ai-guru-fab"
        title="AI गुरूला प्रश्न विचारा"
      >
        <Sparkles size={24} className="text-white" />
      </button>
    </div>
  );
}

// ── Helper Components ────────────────────────────────

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  gradient: string;
  iconColor: string;
}

function StatCard({ icon, label, value, gradient, iconColor }: StatCardProps) {
  return (
    <div className={`glass-card p-4 bg-gradient-to-br ${gradient}`}>
      <div className={`${iconColor} mb-2`}>{icon}</div>
      <div className="text-lg font-bold font-marathi">{value}</div>
      <div className="text-[11px] text-white/40 font-marathi">{label}</div>
    </div>
  );
}

interface ModuleCardProps {
  icon: React.ReactNode;
  title: string;
  desc: string;
  gradient: string;
  onClick?: () => void;
  comingSoon?: boolean;
  badge?: string;
}

function ModuleCard({ icon, title, desc, gradient, onClick, comingSoon, badge }: ModuleCardProps) {
  return (
    <button
      onClick={comingSoon ? undefined : onClick}
      disabled={comingSoon}
      className={`glass-card p-6 bg-gradient-to-br ${gradient} text-left w-full
                  hover:border-white/20 transition-all duration-300 group
                  ${comingSoon ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="text-white/80 group-hover:text-white transition-colors">
          {icon}
        </div>
        {badge && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300">
            {badge}
          </span>
        )}
        {comingSoon && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/30">
            लवकरच
          </span>
        )}
      </div>
      <h3 className="font-semibold font-marathi text-lg mb-1">{title}</h3>
      <p className="text-white/40 text-sm font-marathi">{desc}</p>
    </button>
  );
}

// ── Helpers ──────────────────────────────────────────

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'सुप्रभात';
  if (hour < 17) return 'नमस्कार';
  return 'शुभ संध्याकाळ';
}
