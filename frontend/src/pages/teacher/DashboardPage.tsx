/**
 * Teacher Dashboard — functional dashboard with real stats.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, Calendar, ClipboardList, BarChart3, Brain,
  TrendingUp, Zap, CheckCircle,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import apiClient from '../../api/client';

interface DashboardStats {
  total_students: number;
  active_today: number;
  total_assignments: number;
  avg_attendance_pct: number;
  ai_conversations_today: number;
}

export function TeacherDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      const { data } = await apiClient.get('/teachers/dashboard');
      if (data.stats) setStats(data.stats);
    } catch { /* defaults */ }
  }

  const greeting = getGreeting();

  return (
    <div className="p-8 animate-fade-in" id="teacher-dashboard">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold font-marathi">
          {greeting}, {user?.full_name || 'शिक्षक'} 👨‍🏫
        </h1>
        <p className="text-white/40 mt-1 font-marathi text-sm">तुमच्या वर्गाचे व्यवस्थापन</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Users size={20} />}
          label="एकूण विद्यार्थी"
          value={`${stats?.total_students || 0}`}
          gradient="from-blue-500/20 to-cyan-500/10"
          iconColor="text-blue-400"
        />
        <StatCard
          icon={<Zap size={20} />}
          label="आज सक्रिय"
          value={`${stats?.active_today || 0}`}
          gradient="from-emerald-500/20 to-green-500/10"
          iconColor="text-emerald-400"
        />
        <StatCard
          icon={<CheckCircle size={20} />}
          label="उपस्थिती %"
          value={`${stats?.avg_attendance_pct || 0}%`}
          gradient="from-purple-500/20 to-brand-500/10"
          iconColor="text-purple-400"
        />
        <StatCard
          icon={<Brain size={20} />}
          label="AI संवाद आज"
          value={`${stats?.ai_conversations_today || 0}`}
          gradient="from-orange-500/20 to-red-500/10"
          iconColor="text-orange-400"
        />
      </div>

      {/* Modules grid */}
      <h2 className="text-lg font-semibold font-marathi mb-4 flex items-center gap-2 text-white/80">
        <TrendingUp size={18} />
        व्यवस्थापन मॉड्यूल
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <ModuleCard
          icon={<Users size={28} />}
          title="वर्ग यादी"
          desc="विद्यार्थ्यांची यादी आणि प्रोफाइल पहा"
          gradient="from-blue-500/20 to-blue-600/10"
          onClick={() => navigate('/teacher/roster')}
        />
        <ModuleCard
          icon={<Calendar size={28} />}
          title="उपस्थिती"
          desc="आजची उपस्थिती नोंदवा"
          gradient="from-green-500/20 to-green-600/10"
          onClick={() => navigate('/teacher/attendance')}
          badge="✅ तयार"
        />
        <ModuleCard
          icon={<BarChart3 size={28} />}
          title="विद्यार्थी प्रगती"
          desc="सामर्थ्य/कमकुवतपणा विश्लेषण पहा"
          gradient="from-purple-500/20 to-purple-600/10"
          onClick={() => navigate('/teacher/progress')}
        />
        <ModuleCard
          icon={<Brain size={28} />}
          title="AI वापर"
          desc="विद्यार्थी काय विचारत आहेत ते पहा"
          gradient="from-pink-500/20 to-pink-600/10"
          onClick={() => navigate('/teacher/ai-usage')}
          badge="🤖 नवीन"
        />
        <ModuleCard
          icon={<ClipboardList size={28} />}
          title="असाइनमेंट"
          desc="गृहपाठ आणि चाचण्या तयार करा"
          gradient="from-yellow-500/20 to-yellow-600/10"
          onClick={() => navigate('/teacher/assignments')}
        />
      </div>
    </div>
  );
}

// ── Helper components ────────────────────────────────

function StatCard({ icon, label, value, gradient, iconColor }: {
  icon: React.ReactNode; label: string; value: string; gradient: string; iconColor: string;
}) {
  return (
    <div className={`glass-card p-4 bg-gradient-to-br ${gradient}`}>
      <div className={`${iconColor} mb-2`}>{icon}</div>
      <div className="text-lg font-bold font-marathi">{value}</div>
      <div className="text-[11px] text-white/40 font-marathi">{label}</div>
    </div>
  );
}

function ModuleCard({ icon, title, desc, gradient, onClick, badge }: {
  icon: React.ReactNode; title: string; desc: string; gradient: string;
  onClick?: () => void; badge?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`glass-card p-6 bg-gradient-to-br ${gradient} text-left w-full
                  hover:border-white/20 transition-all duration-300 group cursor-pointer`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="text-white/80 group-hover:text-white transition-colors">{icon}</div>
        {badge && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300">{badge}</span>
        )}
      </div>
      <h3 className="font-semibold font-marathi text-lg mb-1">{title}</h3>
      <p className="text-white/40 text-sm font-marathi">{desc}</p>
    </button>
  );
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'सुप्रभात';
  if (hour < 17) return 'नमस्कार';
  return 'शुभ संध्याकाळ';
}
