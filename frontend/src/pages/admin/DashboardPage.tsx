/**
 * Admin Dashboard — functional dashboard with stats and module navigation.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Users, GraduationCap, TrendingUp, UserCheck } from 'lucide-react';

import apiClient from '../../api/client';

interface DashboardStats {
  total_users: number;
  total_students: number;
  total_teachers: number;
  total_parents: number;
  total_subjects: number;
  total_classes: number;
}

export function AdminDashboard() {

  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    try {
      const { data } = await apiClient.get('/admin/dashboard');
      if (data.stats) setStats(data.stats);
    } catch { /* defaults */ }
  }

  return (
    <div className="p-8 animate-fade-in" id="admin-dashboard">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">⚙️ Admin Dashboard</h1>
        <p className="text-white/40 mt-1">Platform management</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <StatCard icon={<Users size={18} />} label="Total Users" value={`${stats?.total_users || 0}`}
          gradient="from-blue-500/20 to-blue-600/10" />
        <StatCard icon={<GraduationCap size={18} />} label="Students" value={`${stats?.total_students || 0}`}
          gradient="from-emerald-500/20 to-green-500/10" />
        <StatCard icon={<UserCheck size={18} />} label="Teachers" value={`${stats?.total_teachers || 0}`}
          gradient="from-purple-500/20 to-brand-500/10" />
        <StatCard icon={<Users size={18} />} label="Parents" value={`${stats?.total_parents || 0}`}
          gradient="from-orange-500/20 to-red-500/10" />
        <StatCard icon={<BookOpen size={18} />} label="Subjects" value={`${stats?.total_subjects || 0}`}
          gradient="from-cyan-500/20 to-blue-500/10" />
        <StatCard icon={<TrendingUp size={18} />} label="Classes" value={`${stats?.total_classes || 0}`}
          gradient="from-pink-500/20 to-rose-500/10" />
      </div>

      {/* Modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <ModuleCard icon={<BookOpen size={28} />} title="Syllabus Management"
          desc="Subjects, chapters, topics CRUD" gradient="from-blue-500/20 to-blue-600/10"
          onClick={() => navigate('/admin/syllabus')} />
        <ModuleCard icon={<Users size={28} />} title="User Management"
          desc="Search, edit, activate/deactivate users" gradient="from-green-500/20 to-green-600/10"
          onClick={() => navigate('/admin/users')} />
        <ModuleCard icon={<GraduationCap size={28} />} title="Class Management"
          desc="Classes, sections, teacher assignments" gradient="from-purple-500/20 to-purple-600/10"
          onClick={() => navigate('/admin/classes')} />
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, gradient }: {
  icon: React.ReactNode; label: string; value: string; gradient: string;
}) {
  return (
    <div className={`glass-card p-3 bg-gradient-to-br ${gradient} text-center`}>
      <div className="text-white/40 mb-1 flex justify-center">{icon}</div>
      <div className="text-lg font-bold">{value}</div>
      <div className="text-[9px] text-white/30">{label}</div>
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
      <h3 className="font-semibold text-lg mb-1">{title}</h3>
      <p className="text-white/40 text-sm">{desc}</p>
    </button>
  );
}
