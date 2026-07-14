/**
 * ProtectedRoute — checks authentication and role, redirects if unauthorized.
 */
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles: string[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-950">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    // Redirect to appropriate dashboard based on role
    const rolePaths: Record<string, string> = {
      student: '/student',
      teacher: '/teacher',
      parent: '/parent',
      admin: '/admin',
      super_admin: '/super-admin',
    };
    return <Navigate to={rolePaths[user.role] || '/login'} replace />;
  }

  return <>{children}</>;
}
