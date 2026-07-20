/**
 * Super Admin Dashboard — functional with stats and module navigation.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield, DollarSign, MessageCircle, FileText, BarChart3, Settings,
} from 'lucide-react';

import apiClient from '../../api/client';

interface DashboardStats {
  total_users: number; active_users: number;
  total_cost_inr: number; total_cost_usd: number;
  cache_hit_rate: number; total_conversations: number;
  flagged_conversations: number; total_ai_requests: number;
}

export function SuperAdminDashboard() {

  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    try {
      const { data } = await apiClient.get('/super-admin/dashboard');
      if (data.stats) setStats(data.stats);
    } catch { /* defaults */ }
  }

  return (
    <div className="p-8 animate-fade-in" id="superadmin-dashboard">
      <div className="flex items-center gap-3 mb-8">
        <Shield size={28} className="text-brand-400" />
        <div>
          <h1 className="text-2xl font-bold">Super Admin</h1>
          <p className="text-white/40 text-sm">Full platform oversight and control</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Users" value={`${stats?.total_users || 0}`} sub={`${stats?.active_users || 0} active`}
          gradient="from-blue-500/20 to-cyan-500/10" />
        <StatCard label="AI Cost (₹)" value={`₹${(stats?.total_cost_inr || 0).toFixed(2)}`} sub={`$${(stats?.total_cost_usd || 0).toFixed(4)}`}
          gradient="from-green-500/20 to-emerald-500/10" />
        <StatCard label="Cache Hit Rate" value={`${stats?.cache_hit_rate || 0}%`} sub={`${stats?.total_ai_requests || 0} requests`}
          gradient="from-purple-500/20 to-brand-500/10" />
        <StatCard label="Flagged Chats" value={`${stats?.flagged_conversations || 0}`}
          sub={`of ${stats?.total_conversations || 0} total`}
          gradient="from-red-500/20 to-orange-500/10"
          alert={!!stats?.flagged_conversations && stats.flagged_conversations > 0} />
      </div>

      {/* Modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <ModuleCard icon={<DollarSign size={28} />} title="AI Cost Dashboard"
          desc="Tokens + ₹, cache-hit rate, per-user breakdown"
          gradient="from-green-500/20 to-green-600/10" onClick={() => navigate('/super-admin/ai-costs')} />
        <ModuleCard icon={<MessageCircle size={28} />} title="Chat Audit"
          desc="Full AI conversation audit log"
          gradient="from-red-500/20 to-red-600/10" onClick={() => navigate('/super-admin/chat-audit')}
          badge={stats?.flagged_conversations ? `⚠️ ${stats.flagged_conversations}` : undefined} />
        <ModuleCard icon={<Settings size={28} />} title="Master Data"
          desc="Subjects, boards, grades"
          gradient="from-blue-500/20 to-blue-600/10" onClick={() => navigate('/super-admin/master-data')} />
        <ModuleCard icon={<FileText size={28} />} title="Homepage CMS"
          desc="Manage marketing content"
          gradient="from-purple-500/20 to-purple-600/10" onClick={() => navigate('/super-admin/cms')} />
        <ModuleCard icon={<BarChart3 size={28} />} title="Audit Logs"
          desc="Admin action audit trail"
          gradient="from-yellow-500/20 to-yellow-600/10" onClick={() => navigate('/super-admin/audit-logs')} />
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, gradient, alert }: {
  label: string; value: string; sub: string; gradient: string; alert?: boolean;
}) {
  return (
    <div className={`glass-card p-4 bg-gradient-to-br ${gradient} ${alert ? 'border border-red-500/30' : ''}`}>
      <div className="text-lg font-bold">{value}</div>
      <div className="text-[11px] text-white/40">{label}</div>
      <div className="text-[9px] text-white/20 mt-1">{sub}</div>
    </div>
  );
}

function ModuleCard({ icon, title, desc, gradient, onClick, badge }: {
  icon: React.ReactNode; title: string; desc: string; gradient: string; onClick?: () => void; badge?: string;
}) {
  return (
    <button onClick={onClick}
      className={`glass-card p-6 bg-gradient-to-br ${gradient} text-left w-full hover:border-white/20 transition-all duration-300 group cursor-pointer`}>
      <div className="flex items-start justify-between mb-4">
        <div className="text-white/80 group-hover:text-white transition-colors">{icon}</div>
        {badge && <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/20 text-red-300">{badge}</span>}
      </div>
      <h3 className="font-semibold text-lg mb-1">{title}</h3>
      <p className="text-white/40 text-sm">{desc}</p>
    </button>
  );
}
