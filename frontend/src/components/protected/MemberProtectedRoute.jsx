import React from 'react';
import { useSelector } from 'react-redux';
import { Navigate } from 'react-router-dom';

const MemberProtectedRoute = ({ children, fallbackPath = '/login' }) => {
  const { isAuthenticated, loading, roles, role, rolesLoaded } = useSelector((state) => state.auth);

  // Show loading spinner while checking authentication or loading roles
  if (loading || !rolesLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading member access...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={fallbackPath} replace />;
  }

  // Check if user is member, manager, or admin (only after roles are loaded)
  if (rolesLoaded) {
    if (role !== 'member' && role !== 'manager' && role !== 'admin') {
      return <Navigate to="/unauthorized" replace />;
    }

    if (!roles.is_member && !roles.is_manager && !roles.is_admin) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return children;
};

export default MemberProtectedRoute;
