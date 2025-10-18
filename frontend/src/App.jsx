import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Provider } from 'react-redux'
import { Toaster } from 'react-hot-toast'
import { store } from './store'
import AuthInitializer from './components/AuthInitializer'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterWithInvitation from './pages/RegisterWithInvitation'
import AdminDashboard from './pages/AdminDashboard'
import ManagerDashboard from './pages/ManagerDashboard'
import MemberDashboard from './pages/MemberDashboard'
import UnauthorizedPage from './pages/UnauthorizedPage'
import { AdminProtectedRoute, ManagerProtectedRoute, MemberProtectedRoute } from './components/protected'
import './App.css'

function App() {
  return (
    <Provider store={store}>
      <AuthInitializer>
        <div className="App">
          <Router>
            <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterWithInvitation />} />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />
            
            {/* Protected Routes */}
            <Route 
              path="/admin-dashboard" 
              element={
                <AdminProtectedRoute>
                  <AdminDashboard />
                </AdminProtectedRoute>
              } 
            />
            <Route 
              path="/manager-dashboard" 
              element={
                <ManagerProtectedRoute>
                  <ManagerDashboard />
                </ManagerProtectedRoute>
              } 
            />
            <Route 
              path="/member-dashboard" 
              element={
                <MemberProtectedRoute>
                  <MemberDashboard />
                </MemberProtectedRoute>
              } 
            />
            </Routes>
          </Router>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#4ade80',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </AuthInitializer>
    </Provider>
  )
}

export default App