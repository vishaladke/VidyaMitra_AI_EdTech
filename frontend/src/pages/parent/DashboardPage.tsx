/**
 * Parent Dashboard — functional dashboard with children overview.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, BarChart3, FileText, Bell, Flame, MessageCircle, Zap,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import apiClient from '../../api/client';

interface DashboardStats {
  total_children: number;
  active_today: number;
  total_ai_conversations: number;
  avg_streak: number;
}

interface Child {
  id: string;
  full_name: string;
  grade: number | null;
  streak_days: number;
  relationship: string;
}

export function ParentDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [children, setChildren] = useState<Child[]>([]);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    try {
      const { data } = await apiClient.get('/parents/dashboard');
      if (data.stats) setStats(data.stats);
      if (data.children) setChildren(data.children);
    } catch { /* defaults */ }
  }

  const greeting = getGreeting();

  return (
    <div className="p-8 animate-fade-in" id="parent-dashboard">
      <div className="mb-8">
        <h1 className="text-2xl font-bold font-marathi">
          {greeting}, {user?.full_name || 'पालक'} 👨‍👧‍👦
        </h1>
        <p className="text-white/40 mt-1 font-marathi text-sm">तुमच्या मुलांची प्रगती पहा</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard icon={<Users size={20} />} label="मुले" value={`${stats?.total_children || 0}`}
          gradient="from-blue-500/20 to-cyan-500/10" iconColor="text-blue-400" />
        <StatCard icon={<Zap size={20} />} label="आज सक्रिय" value={`${stats?.active_today || 0}`}
          gradient="from-emerald-500/20 to-green-500/10" iconColor="text-emerald-400" />
        <StatCard icon={<MessageCircle size={20} />} label="AI संवाद" value={`${stats?.total_ai_conversations || 0}`}
          gradient="from-purple-500/20 to-brand-500/10" iconColor="text-purple-400" />
        <StatCard icon={<Flame size={20} />} label="सरासरी स्ट्रीक" value={`${stats?.avg_streak || 0} दिवस`}
          gradient="from-orange-500/20 to-red-500/10" iconColor="text-orange-400" />
      </div>

      {/* Children list */}
      {children.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold font-marathi mb-4 text-white/80">तुमची मुले</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {children.map(child => (
              <button
                key={child.id}
                onClick={() => navigate(`/parent/children/${child.id}`)}
                className="glass-card p-5 bg-gradient-to-br from-brand-500/10 to-purple-600/5 text-left
                           hover:border-white/20 transition-all duration-300 group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-brand-500/20 to-purple-600/20 flex items-center justify-center text-xl">
                    🎓
                  </div>
                  <div>
                    <h3 className="font-semibold font-marathi group-hover:text-white transition-colors">{child.full_name}</h3>
                    <p className="text-xs text-white/30">इयत्ता {child.grade} • {child.relationship}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-4">
                  <span className="text-xs text-orange-400 flex items-center gap-1">
                    <Flame size={12} /> {child.streak_days} दिवस स्ट्रीक
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Module cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <ModuleCard icon={<BarChart3 size={28} />} title="प्रगती" desc="सामर्थ्य/कमकुवतपणा पहा"
          gradient="from-green-500/20 to-green-600/10" onClick={() => navigate('/parent/progress')} />
        <ModuleCard icon={<FileText size={28} />} title="साप्ताहिक अहवाल" desc="WhatsApp अहवालाची प्रत"
          gradient="from-purple-500/20 to-purple-600/10" onClick={() => navigate('/parent/reports')} />
        <ModuleCard icon={<Bell size={28} />} title="सूचना" desc="सूचना प्राधान्ये सेट करा"
          gradient="from-yellow-500/20 to-yellow-600/10" onClick={() => navigate('/parent/notifications')} />
      </div>
    </div>
  );
}

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

function ModuleCard({ icon, title, desc, gradient, onClick }: {
  icon: React.ReactNode; title: string; desc: string; gradient: string; onClick?: () => void;
}) {
  return (
    <button onClick={onClick}
      className={`glass-card p-6 bg-gradient-to-br ${gradient} text-left w-full hover:border-white/20 transition-all duration-300 group cursor-pointer`}>
      <div className="text-white/80 group-hover:text-white transition-colors mb-4">{icon}</div>
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
