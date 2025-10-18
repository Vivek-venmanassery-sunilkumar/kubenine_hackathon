import React from 'react';
import { useSelector } from 'react-redux';
import { Navigate } from 'react-router-dom';

const ManagerProtectedRoute = ({ children, fallbackPath = '/login' }) => {
  const { isAuthenticated, loading, roles, role } = useSelector((state) => state.auth);

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading manager access...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={fallbackPath} replace />;
  }

  // Check if user is manager or admin (admin can access manager routes)
  if (role !== 'manager' && role !== 'admin') {
    return <Navigate to="/unauthorized" replace />;
  }

  if (!roles.is_manager && !roles.is_admin) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

export default ManagerProtectedRoute;
