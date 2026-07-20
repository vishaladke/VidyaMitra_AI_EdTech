/**
 * App.tsx — Top-level routes with role-based routing and RBAC.
 * 
 * Super Admin routes are NOT at a standard path — they use the
 * SUPERADMIN_URL_PATH env var, but on the frontend we use a
 * fixed /super-admin path since the backend API prefix handles isolation.
 */
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { LoginPage } from './components/auth/LoginPage';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AppShell } from './components/layout/AppShell';
import { HomePage } from './pages/public/HomePage';
import { StudentDashboard } from './pages/student/DashboardPage';
import { AIGuruPage } from './pages/student/AIGuruPage';
import { SyllabusPage } from './pages/student/SyllabusPage';
import { TeacherDashboard } from './pages/teacher/DashboardPage';
import { AttendancePage } from './pages/teacher/AttendancePage';
import { StudentProgressPage } from './pages/teacher/StudentProgressPage';
import { AIUsagePage } from './pages/teacher/AIUsagePage';
import { ParentDashboard } from './pages/parent/DashboardPage';
import { ChildProgressPage } from './pages/parent/ChildProgressPage';
import { ReportsPage } from './pages/parent/ReportsPage';
import { AdminDashboard } from './pages/admin/DashboardPage';
import { SyllabusCRUDPage } from './pages/admin/SyllabusCRUDPage';
import { UserManagementPage } from './pages/admin/UserManagementPage';
import { ClassManagementPage } from './pages/admin/ClassManagementPage';
import { SuperAdminDashboard } from './pages/superadmin/DashboardPage';
import { AICostDashboardPage } from './pages/superadmin/AICostDashboardPage';
import { ChatAuditPage } from './pages/superadmin/ChatAuditPage';
import { MasterDataPage } from './pages/superadmin/MasterDataPage';

function AuthRedirect() {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated || !user) return <Navigate to="/login" />;
  const paths: Record<string, string> = {
    student: '/student',
    teacher: '/teacher',
    parent: '/parent',
    admin: '/admin',
    super_admin: '/super-admin',
  };
  return <Navigate to={paths[user.role] || '/login'} />;
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />

      {/* Auth redirect */}
      <Route path="/dashboard" element={<AuthRedirect />} />

      {/* Student */}
      <Route
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/student/syllabus" element={<SyllabusPage />} />
        <Route path="/student/ai-guru" element={<AIGuruPage />} />
        <Route path="/student/*" element={<StudentDashboard />} />
      </Route>

      {/* Teacher */}
      <Route
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/teacher" element={<TeacherDashboard />} />
        <Route path="/teacher/attendance" element={<AttendancePage />} />
        <Route path="/teacher/progress" element={<StudentProgressPage />} />
        <Route path="/teacher/roster" element={<StudentProgressPage />} />
        <Route path="/teacher/ai-usage" element={<AIUsagePage />} />
        <Route path="/teacher/*" element={<TeacherDashboard />} />
      </Route>

      {/* Parent */}
      <Route
        element={
          <ProtectedRoute allowedRoles={['parent']}>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/parent" element={<ParentDashboard />} />
        <Route path="/parent/children/:childId" element={<ChildProgressPage />} />
        <Route path="/parent/progress" element={<ChildProgressPage />} />
        <Route path="/parent/reports" element={<ReportsPage />} />
        <Route path="/parent/*" element={<ParentDashboard />} />
      </Route>

      {/* Admin */}
      <Route
        element={
          <ProtectedRoute allowedRoles={['admin', 'super_admin']}>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/syllabus" element={<SyllabusCRUDPage />} />
        <Route path="/admin/users" element={<UserManagementPage />} />
        <Route path="/admin/classes" element={<ClassManagementPage />} />
        <Route path="/admin/*" element={<AdminDashboard />} />
      </Route>

      {/* Super Admin — NOT linked from any public navigation */}
      <Route
        element={
          <ProtectedRoute allowedRoles={['super_admin']}>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/super-admin" element={<SuperAdminDashboard />} />
        <Route path="/super-admin/ai-costs" element={<AICostDashboardPage />} />
        <Route path="/super-admin/chat-audit" element={<ChatAuditPage />} />
        <Route path="/super-admin/master-data" element={<MasterDataPage />} />
        <Route path="/super-admin/*" element={<SuperAdminDashboard />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
