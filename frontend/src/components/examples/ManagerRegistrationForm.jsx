import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import authService from '../../services/authService';
import { ERROR_TYPES } from '../../utils/errorHandler';

/**
 * Example component showing how to use the standardized error handling
 */
const ManagerRegistrationForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [fieldErrors, setFieldErrors] = useState({});
  
  const dispatch = useDispatch();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear field-specific errors when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous errors
    setErrors({});
    setFieldErrors({});
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await authService.registerManager(
        formData.email,
        formData.password,
        formData.name
      );
      
      // Success - show success message and call onSuccess
      console.log('Manager registered successfully:', response);
      onSuccess?.(response);
      
    } catch (error) {
      console.error('Registration error:', error);
      
      // Handle different types of errors
      if (error.message.includes('email already exists')) {
        // Handle conflict error (duplicate email)
        setFieldErrors({
          email: 'A manager with this email already exists'
        });
      } else if (error.message.includes('required')) {
        // Handle validation errors
        const errorDetails = authService.getErrorDetails(error);
        if (errorDetails.field_errors) {
          setFieldErrors(errorDetails.field_errors);
        }
      } else {
        // Handle other errors
        setErrors({ general: error.message });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Register Manager</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* General Error Display */}
        {errors.general && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {errors.general}
          </div>
        )}
        
        {/* Name Field */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Name
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
              errors.name || fieldErrors.name ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter manager name"
          />
          {(errors.name || fieldErrors.name) && (
            <p className="mt-1 text-sm text-red-600">
              {errors.name || fieldErrors.name}
            </p>
          )}
        </div>
        
        {/* Email Field */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
              errors.email || fieldErrors.email ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter email address"
          />
          {(errors.email || fieldErrors.email) && (
            <p className="mt-1 text-sm text-red-600">
              {errors.email || fieldErrors.email}
            </p>
          )}
        </div>
        
        {/* Password Field */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Password
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
              errors.password || fieldErrors.password ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter password"
          />
          {(errors.password || fieldErrors.password) && (
            <p className="mt-1 text-sm text-red-600">
              {errors.password || fieldErrors.password}
            </p>
          )}
        </div>
        
        {/* Submit Button */}
        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Registering...' : 'Register Manager'}
          </button>
          
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default ManagerRegistrationForm;
