import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { useEffect } from 'react';
import '../App.css'

function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated, role, loading } = useSelector((state) => state.auth);

  // Check authentication status on component mount
  useEffect(() => {
    if (isAuthenticated && !loading) {
      // If user is authenticated, redirect to appropriate dashboard
      if (role === 'admin') {
        navigate('/admin-dashboard');
      } else if (role === 'manager') {
        navigate('/manager-dashboard');
      } else if (role === 'member') {
        navigate('/member-dashboard');
      }
    }
  }, [isAuthenticated, role, loading, navigate]);
  return (
    <div className="min-h-screen w-screen overflow-x-hidden">
      {/* Hero Section */}
      <header className="relative w-screen min-h-screen bg-gradient-to-br from-amber-50 via-stone-100 to-neutral-200 flex items-center justify-center">
        <div className="absolute inset-0 bg-black opacity-5"></div>
        <div className="relative z-10 w-full px-4 sm:px-6 lg:px-8 text-center">
          <div className="space-y-8">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-black leading-tight">
              On Call 24/7
            </h1>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-light text-gray-800 italic">
              Your call, our responsibility
            </h2>
            <p className="text-lg sm:text-xl lg:text-2xl text-gray-700 max-w-4xl mx-auto leading-relaxed">
              Professional on-call scheduling and management for organizations and teams. 
              Never miss a critical incident with our intelligent rotation system.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-8">
              {isAuthenticated ? (
                <button 
                  onClick={() => {
                    if (role === 'admin') {
                      navigate('/admin-dashboard');
                    } else if (role === 'manager') {
                      navigate('/manager-dashboard');
                    } else {
                      navigate('/member-dashboard');
                    }
                  }}
                  className="btn-primary w-full sm:w-auto"
                >
                  Go to Dashboard
                </button>
              ) : (
                <>
                  <button 
                    onClick={() => navigate('/login')}
                    className="btn-primary w-full sm:w-auto"
                  >
                    Login
                  </button>
                  <button className="btn-secondary w-full sm:w-auto">
                    Learn More
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Features Section */}
      <section className="w-screen py-20 bg-stone-50">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h3 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-black mb-4">
              Why Choose On Call 24/7?
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-amber-50 p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-amber-200">
              <div className="text-5xl mb-6 text-center">🔄</div>
              <h4 className="text-xl font-semibold text-black mb-4 text-center">
                Smart Rotations
              </h4>
              <p className="text-gray-700 text-center leading-relaxed">
                Automated scheduling with intelligent load balancing and conflict resolution.
              </p>
            </div>
            <div className="bg-amber-50 p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-amber-200">
              <div className="text-5xl mb-6 text-center">📱</div>
              <h4 className="text-xl font-semibold text-black mb-4 text-center">
                Multi-Channel Alerts
              </h4>
              <p className="text-gray-700 text-center leading-relaxed">
                Get notified via SMS, email, Slack, and more when incidents occur.
              </p>
            </div>
            <div className="bg-amber-50 p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-amber-200">
              <div className="text-5xl mb-6 text-center">👥</div>
              <h4 className="text-xl font-semibold text-black mb-4 text-center">
                Team Management
              </h4>
              <p className="text-gray-700 text-center leading-relaxed">
                Organize teams, manage permissions, and track availability seamlessly.
              </p>
            </div>
            <div className="bg-amber-50 p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-amber-200">
              <div className="text-5xl mb-6 text-center">📊</div>
              <h4 className="text-xl font-semibold text-black mb-4 text-center">
                Analytics & Reporting
              </h4>
              <p className="text-gray-700 text-center leading-relaxed">
                Comprehensive insights into on-call patterns and team performance.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-screen bg-black text-amber-50 py-12">
        <div className="w-full px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-amber-100">
            &copy; 2024 On Call 24/7. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
