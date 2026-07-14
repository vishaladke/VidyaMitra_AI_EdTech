/**
 * AppShell — sidebar + topbar + content area.
 * Sidebar is role-aware: shows only the links for the current user's role.
 */
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
  BookOpen, GraduationCap, ClipboardList, MessageCircle, BarChart3,
  Users, Calendar, Brain, FileText, Settings, LogOut, Home, Shield, DollarSign,
  Bell,
} from 'lucide-react';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: Record<string, NavItem[]> = {
  student: [
    { label: 'डॅशबोर्ड', path: '/student', icon: <Home size={20} /> },
    { label: 'अभ्यासक्रम', path: '/student/syllabus', icon: <BookOpen size={20} /> },
    { label: 'असाइनमेंट', path: '/student/assignments', icon: <ClipboardList size={20} /> },
    { label: 'चाचण्या', path: '/student/tests', icon: <FileText size={20} /> },
    { label: 'AI गुरू', path: '/student/ai-guru', icon: <MessageCircle size={20} /> },
    { label: 'प्रगती', path: '/student/progress', icon: <BarChart3 size={20} /> },
  ],
  teacher: [
    { label: 'डॅशबोर्ड', path: '/teacher', icon: <Home size={20} /> },
    { label: 'वर्ग यादी', path: '/teacher/roster', icon: <Users size={20} /> },
    { label: 'उपस्थिती', path: '/teacher/attendance', icon: <Calendar size={20} /> },
    { label: 'चाचण्या', path: '/teacher/tests', icon: <ClipboardList size={20} /> },
    { label: 'विद्यार्थी प्रगती', path: '/teacher/progress', icon: <BarChart3 size={20} /> },
    { label: 'AI वापर', path: '/teacher/ai-usage', icon: <Brain size={20} /> },
  ],
  parent: [
    { label: 'डॅशबोर्ड', path: '/parent', icon: <Home size={20} /> },
    { label: 'मुले', path: '/parent/children', icon: <Users size={20} /> },
    { label: 'प्रगती', path: '/parent/progress', icon: <BarChart3 size={20} /> },
    { label: 'अहवाल', path: '/parent/reports', icon: <FileText size={20} /> },
    { label: 'सूचना', path: '/parent/notifications', icon: <Bell size={20} /> },
  ],
  admin: [
    { label: 'डॅशबोर्ड', path: '/admin', icon: <Home size={20} /> },
    { label: 'अभ्यासक्रम', path: '/admin/syllabus', icon: <BookOpen size={20} /> },
    { label: 'वापरकर्ते', path: '/admin/users', icon: <Users size={20} /> },
    { label: 'वर्ग', path: '/admin/classes', icon: <GraduationCap size={20} /> },
    { label: 'सेटिंग्ज', path: '/admin/settings', icon: <Settings size={20} /> },
  ],
  super_admin: [
    { label: 'Dashboard', path: '/super-admin', icon: <Home size={20} /> },
    { label: 'Master Data', path: '/super-admin/master-data', icon: <Settings size={20} /> },
    { label: 'AI Cost', path: '/super-admin/ai-cost', icon: <DollarSign size={20} /> },
    { label: 'Chat Audit', path: '/super-admin/chat-audit', icon: <MessageCircle size={20} /> },
    { label: 'CMS', path: '/super-admin/cms', icon: <FileText size={20} /> },
    { label: 'Reports', path: '/super-admin/reports', icon: <BarChart3 size={20} /> },
    { label: 'Security', path: '/super-admin/security', icon: <Shield size={20} /> },
  ],
};

const ROLE_LABELS: Record<string, string> = {
  student: '🎓 विद्यार्थी',
  teacher: '👨‍🏫 शिक्षक',
  parent: '👨‍👧‍👦 पालक',
  admin: '⚙️ Admin',
  super_admin: '🛡️ Super Admin',
};

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  if (!user) return null;

  const navItems = NAV_ITEMS[user.role] || [];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-surface-950 flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 bg-surface-900/50 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-white/5">
          <h1 className="text-xl font-bold font-marathi bg-gradient-to-r from-brand-400 to-brand-600 bg-clip-text text-transparent">
            विद्यामित्र
          </h1>
          <p className="text-xs text-white/40 mt-1">{ROLE_LABELS[user.role]}</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`nav-item w-full ${
                location.pathname === item.path ? 'active' : ''
              }`}
            >
              {item.icon}
              <span className="font-marathi text-sm">{item.label}</span>
            </button>
          ))}
        </nav>

        {/* User + Logout */}
        <div className="p-4 border-t border-white/5">
          <div className="text-sm text-white/60 mb-3 truncate font-marathi">
            {user.full_name}
          </div>
          <button
            onClick={handleLogout}
            className="nav-item w-full text-red-400/60 hover:text-red-400 hover:bg-red-500/5"
          >
            <LogOut size={20} />
            <span className="text-sm">बाहेर पडा</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
