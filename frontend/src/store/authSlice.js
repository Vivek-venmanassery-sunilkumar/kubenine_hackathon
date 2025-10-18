import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import authService from '../services/authService';

const initialState = {
  user: null,
  role: null,
  isAuthenticated: false,
  roles: {
    is_admin: false,
    is_manager: false,
    is_member: false,
  },
  loading: false,
  error: null,
};

// Async thunk to get user roles and permissions
export const fetchUserRoles = createAsyncThunk(
  'auth/fetchUserRoles',
  async (_, { rejectWithValue }) => {
    try {
      const rolesData = await authService.getRoles();
      return rolesData;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action) => {
      state.user = action.payload;
      state.isAuthenticated = true;
      state.error = null;
    },
    setRole: (state, action) => {
      state.role = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    logout: (state) => {
      state.user = null;
      state.role = null;
      state.isAuthenticated = false;
      state.roles = {
        is_admin: false,
        is_manager: false,
        is_member: false,
      };
      state.loading = false;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUserRoles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUserRoles.fulfilled, (state, action) => {
        state.loading = false;
        state.roles = {
          is_admin: action.payload.is_admin,
          is_manager: action.payload.is_manager,
          is_member: action.payload.is_member,
        };
        // Update user info if available
        if (action.payload.name || action.payload.email) {
          state.user = {
            ...state.user,
            name: action.payload.name,
            email: action.payload.email,
            id: action.payload.id,
          };
        }
      })
      .addCase(fetchUserRoles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setUser, setRole, setLoading, setError, logout, clearError } = authSlice.actions;
export default authSlice.reducer;
