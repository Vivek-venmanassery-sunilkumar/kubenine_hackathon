import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchUserRoles } from '../store/authSlice';

const AuthInitializer = ({ children }) => {
  const dispatch = useDispatch();
  const { isAuthenticated, loading, rolesLoaded } = useSelector((state) => state.auth);

  useEffect(() => {
    // On app startup, try to fetch user roles to check if user is authenticated
    // This will work with HTTP-only cookies
    if (!isAuthenticated && !loading && !rolesLoaded) {
      dispatch(fetchUserRoles());
    }
  }, [dispatch, isAuthenticated, loading, rolesLoaded]);

  return children;
};

export default AuthInitializer;
