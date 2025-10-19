/**
 * Centralized error handling utility for consistent error management across the frontend.
 */

/**
 * Standard error response structure from the backend
 * @typedef {Object} APIError
 * @property {string} error - Human-readable error message
 * @property {string} error_code - Machine-readable error code
 * @property {Object} details - Additional error details
 */

/**
 * Error types based on HTTP status codes and error codes
 */
export const ERROR_TYPES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  CONFLICT: 'CONFLICT',
  NOT_FOUND: 'NOT_FOUND',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
};

/**
 * Error severity levels
 */
export const ERROR_SEVERITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

/**
 * Parse API error response and extract structured error information
 * @param {Response} response - Fetch response object
 * @param {Object} errorData - Parsed error data from response
 * @returns {Object} Structured error object
 */
export const parseAPIError = async (response, errorData = null) => {
  try {
    // If errorData is not provided, try to parse it from response
    if (!errorData) {
      errorData = await response.json();
    }


    const status = response.status;
    let errorCode = 'UNKNOWN_ERROR';
    let message = 'An unexpected error occurred';
    let details = {};

    // Handle our custom error format
    if (errorData?.error_code) {
      errorCode = errorData.error_code;
      message = errorData.error;
      details = errorData.details || {};
    }
    // Handle Django REST Framework error format
    else if (errorData?.detail) {
      message = errorData.detail;
      errorCode = errorData.code || 'DRF_ERROR';
      
      // Handle specific DRF error types
      if (errorData.code === 'token_not_valid') {
        errorCode = 'TOKEN_INVALID';
        message = 'Your session has expired. Please log in again.';
      } else if (errorData.code === 'authentication_failed') {
        errorCode = 'AUTH_FAILED';
        message = 'Authentication failed. Please check your credentials.';
      } else if (errorData.code === 'permission_denied') {
        errorCode = 'PERMISSION_DENIED';
        message = 'You do not have permission to perform this action.';
      }
      
      // Include additional details from DRF
      if (errorData.messages) {
        details.messages = errorData.messages;
      }
    }
    // Handle Django form validation errors
    else if (typeof errorData === 'object' && !Array.isArray(errorData)) {
      // Check if it's a field validation error
      const fieldErrors = {};
      let hasFieldErrors = false;
      
      for (const [key, value] of Object.entries(errorData)) {
        if (Array.isArray(value) && value.length > 0) {
          fieldErrors[key] = value[0]; // Take the first error message
          hasFieldErrors = true;
        }
      }
      
      if (hasFieldErrors) {
        errorCode = 'VALIDATION_ERROR';
        // Use the first field error as the main message instead of generic message
        const firstFieldError = Object.values(fieldErrors)[0];
        message = firstFieldError || 'Please correct the errors below.';
        details.field_errors = fieldErrors;
      } else {
        // Try to extract a meaningful message
        const possibleMessages = Object.values(errorData).filter(v => typeof v === 'string');
        if (possibleMessages.length > 0) {
          message = possibleMessages[0];
        }
      }
    }
    // Handle simple string errors
    else if (typeof errorData === 'string') {
      message = errorData;
    }

    // Determine error type based on status code and error code
    let errorType = ERROR_TYPES.UNKNOWN_ERROR;
    let severity = ERROR_SEVERITY.MEDIUM;

    switch (status) {
      case 400:
        errorType = errorCode === 'VALIDATION_ERROR' ? ERROR_TYPES.VALIDATION_ERROR : ERROR_TYPES.UNKNOWN_ERROR;
        severity = ERROR_SEVERITY.LOW;
        break;
      case 401:
        errorType = ERROR_TYPES.UNAUTHORIZED;
        severity = ERROR_SEVERITY.HIGH;
        break;
      case 403:
        errorType = ERROR_TYPES.FORBIDDEN;
        severity = ERROR_SEVERITY.HIGH;
        break;
      case 404:
        errorType = ERROR_TYPES.NOT_FOUND;
        severity = ERROR_SEVERITY.MEDIUM;
        break;
      case 409:
        errorType = ERROR_TYPES.CONFLICT;
        severity = ERROR_SEVERITY.MEDIUM;
        break;
      case 500:
        errorType = ERROR_TYPES.INTERNAL_ERROR;
        severity = ERROR_SEVERITY.CRITICAL;
        break;
      default:
        errorType = ERROR_TYPES.UNKNOWN_ERROR;
        severity = ERROR_SEVERITY.MEDIUM;
    }

    const parsedError = {
      type: errorType,
      severity,
      message,
      details,
      status,
      errorCode,
      timestamp: new Date().toISOString()
    };
    
    
    return parsedError;
  } catch (parseError) {
    // If we can't parse the error, return a generic error
    return {
      type: ERROR_TYPES.UNKNOWN_ERROR,
      severity: ERROR_SEVERITY.MEDIUM,
      message: 'An unexpected error occurred. Please try again.',
      details: { 
        parseError: parseError.message,
        originalResponse: errorData 
      },
      status: response?.status || 0,
      errorCode: 'PARSE_ERROR',
      timestamp: new Date().toISOString()
    };
  }
};

/**
 * Handle network errors (no response received)
 * @param {Error} error - Network error
 * @returns {Object} Structured error object
 */
export const handleNetworkError = (error) => {
  return {
    type: ERROR_TYPES.NETWORK_ERROR,
    severity: ERROR_SEVERITY.HIGH,
    message: 'Network error. Please check your connection and try again.',
    details: { originalError: error.message },
    status: 0,
    errorCode: 'NETWORK_ERROR',
    timestamp: new Date().toISOString()
  };
};

/**
 * Get user-friendly error message based on error type and details
 * @param {Object} error - Structured error object
 * @returns {string} User-friendly error message
 */
export const getErrorMessage = (error) => {
  const { type, message, details, errorCode } = error;

  // Handle validation errors with field-specific messages
  if (type === ERROR_TYPES.VALIDATION_ERROR && details.field_errors) {
    const fieldErrors = Object.entries(details.field_errors)
      .filter(([_, errorMsg]) => errorMsg)
      .map(([field, errorMsg]) => `${field}: ${errorMsg}`)
      .join(', ');
    
    return fieldErrors || message;
  }

  // Handle conflict errors with specific field information
  if (type === ERROR_TYPES.CONFLICT && details.field) {
    return `${message} (${details.field}: ${details.value || 'provided'})`;
  }

  // Handle specific error codes with user-friendly messages
  switch (errorCode) {
    case 'TOKEN_INVALID':
      return 'Your session has expired. Please log in again.';
    case 'AUTH_FAILED':
      return 'Authentication failed. Please check your credentials.';
    case 'PERMISSION_DENIED':
      return 'You do not have permission to perform this action.';
    case 'UNAUTHORIZED':
      // For UNAUTHORIZED errors, return the specific message from backend
      return message || 'You are not authorized to perform this action.';
    case 'DRF_ERROR':
      // For DRF errors, try to make the message more user-friendly
      if (message.includes('token_not_valid')) {
        return 'Your session has expired. Please log in again.';
      } else if (message.includes('authentication_failed')) {
        return 'Authentication failed. Please check your credentials.';
      } else if (message.includes('permission_denied')) {
        return 'You do not have permission to perform this action.';
      }
      break;
    case 'PARSE_ERROR':
      return 'An unexpected error occurred. Please try again.';
  }

  // Return the message as-is for other error types
  return message;
};

/**
 * Determine if an error should be shown to the user
 * @param {Object} error - Structured error object
 * @returns {boolean} Whether to show the error to the user
 */
export const shouldShowError = (error) => {
  const { type, severity } = error;
  
  // Always show validation and conflict errors
  if (type === ERROR_TYPES.VALIDATION_ERROR || type === ERROR_TYPES.CONFLICT) {
    return true;
  }
  
  // Show high severity errors
  if (severity === ERROR_SEVERITY.HIGH || severity === ERROR_SEVERITY.CRITICAL) {
    return true;
  }
  
  // Don't show internal errors to users (log them instead)
  if (type === ERROR_TYPES.INTERNAL_ERROR) {
    return false;
  }
  
  return true;
};

/**
 * Get appropriate action for the user based on error type
 * @param {Object} error - Structured error object
 * @returns {Object} Action object with type and message
 */
export const getErrorAction = (error) => {
  const { type, severity } = error;

  switch (type) {
    case ERROR_TYPES.UNAUTHORIZED:
      return {
        type: 'redirect',
        message: 'Please log in again',
        action: '/login'
      };
    
    case ERROR_TYPES.FORBIDDEN:
      return {
        type: 'redirect',
        message: 'You do not have permission to access this resource',
        action: '/unauthorized'
      };
    
    case ERROR_TYPES.NOT_FOUND:
      return {
        type: 'redirect',
        message: 'The requested resource was not found',
        action: '/404'
      };
    
    case ERROR_TYPES.NETWORK_ERROR:
      return {
        type: 'retry',
        message: 'Please check your connection and try again',
        action: 'retry'
      };
    
    case ERROR_TYPES.INTERNAL_ERROR:
      return {
        type: 'contact_support',
        message: 'An unexpected error occurred. Please contact support if this persists.',
        action: 'contact_support'
      };
    
    default:
      return {
        type: 'dismiss',
        message: 'Please try again',
        action: 'dismiss'
      };
  }
};

/**
 * Log error for debugging purposes
 * @param {Object} error - Structured error object
 * @param {string} context - Context where the error occurred
 */
export const logError = (error, context = 'Unknown') => {
  const logData = {
    context,
    error: {
      type: error.type,
      message: error.message,
      details: error.details,
      status: error.status,
      errorCode: error.errorCode,
      timestamp: error.timestamp
    }
  };

  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.error('API Error:', logData);
  }

  // In production, you might want to send this to a logging service
  // Example: sendToLoggingService(logData);
};

/**
 * Create a standardized error handler for API calls
 * @param {Function} showNotification - Function to show notifications to user
 * @param {Function} navigate - Function to navigate to different routes
 * @returns {Function} Error handler function
 */
export const createErrorHandler = (showNotification, navigate) => {
  return async (error, context = 'API Call') => {
    let structuredError;

    // Handle different types of errors
    if (error instanceof Response) {
      // API response error
      structuredError = await parseAPIError(error);
    } else if (error instanceof Error) {
      // Network or other error
      structuredError = handleNetworkError(error);
    } else {
      // Unknown error type
      structuredError = {
        type: ERROR_TYPES.UNKNOWN_ERROR,
        severity: ERROR_SEVERITY.MEDIUM,
        message: 'An unexpected error occurred',
        details: { originalError: String(error) },
        status: 0,
        errorCode: 'UNKNOWN_ERROR',
        timestamp: new Date().toISOString()
      };
    }

    // Log the error
    logError(structuredError, context);

    // Show error to user if appropriate
    if (shouldShowError(structuredError)) {
      const userMessage = getErrorMessage(structuredError);
      const action = getErrorAction(structuredError);

      // Show notification
      showNotification({
        type: 'error',
        message: userMessage,
        action: action
      });

      // Handle specific actions
      if (action.type === 'redirect' && navigate) {
        navigate(action.action);
      }
    }

    return structuredError;
  };
};

/**
 * Default error handler for common use cases
 */
export const defaultErrorHandler = createErrorHandler(
  (notification) => {
    // Default notification handler - you can replace this with your notification system
    console.error('Error Notification:', notification);
    alert(notification.message); // Replace with proper notification component
  },
  (path) => {
    // Default navigation handler - you can replace this with your router
    console.log('Navigate to:', path);
    window.location.href = path; // Replace with proper router navigation
  }
);
