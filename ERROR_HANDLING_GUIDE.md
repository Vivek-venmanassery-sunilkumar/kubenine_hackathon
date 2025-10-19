# Comprehensive Error Handling Guide

This guide explains the standardized error handling system implemented across the backend and frontend to ensure consistent, user-friendly error messages.

## Overview

The error handling system provides:
- **Consistent error responses** across all API endpoints
- **User-friendly error messages** that are easy to understand
- **Structured error data** for programmatic handling
- **Automatic error categorization** based on HTTP status codes and error types
- **Frontend error handling utilities** for easy integration

## Backend Error Handling

### Error Response Structure

All API endpoints now return errors in a standardized format:

```json
{
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "details": {
    "field": "field_name",
    "value": "provided_value",
    "additional_info": "context_specific_data"
  }
}
```

### Error Types and HTTP Status Codes

| Error Type | HTTP Status | Description | Example |
|------------|-------------|-------------|---------|
| `VALIDATION_ERROR` | 400 | Input validation failed | Missing required fields |
| `CONFLICT` | 409 | Resource conflict | Duplicate email |
| `NOT_FOUND` | 404 | Resource not found | User doesn't exist |
| `UNAUTHORIZED` | 401 | Authentication required | Invalid credentials |
| `FORBIDDEN` | 403 | Access denied | Insufficient permissions |
| `INTERNAL_ERROR` | 500 | Server error | Database connection failed |

### Backend Implementation

#### 1. Error Handling Utility (`hirethon_template/utils/error_handling.py`)

```python
from hirethon_template.utils.error_handling import (
    create_validation_error_response,
    create_conflict_error_response,
    create_unauthorized_error_response,
    handle_database_error
)

# Example usage in API view
@api_view(['POST'])
def register_manager(request):
    try:
        # Business logic here
        user = User.objects.create_user(...)
        return create_created_response("Manager registered successfully", {"user": user_data})
    except IntegrityError as e:
        api_error = handle_database_error(e, "manager registration")
        return Response({
            "error": api_error.message,
            "error_code": api_error.error_code,
            "details": api_error.details
        }, status=api_error.status_code)
```

#### 2. Custom Exception Classes

```python
# Pre-defined exception classes for common scenarios
class ValidationError(APIError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, "VALIDATION_ERROR", details)

class ConflictError(APIError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_409_CONFLICT, "CONFLICT", details)
```

## Frontend Error Handling

### Error Handler Utility (`frontend/src/utils/errorHandler.js`)

The frontend error handler provides:

- **Automatic error parsing** from API responses
- **Error categorization** based on status codes and error codes
- **User-friendly message generation** with field-specific details
- **Error action suggestions** (retry, redirect, contact support)
- **Logging capabilities** for debugging

### Usage Examples

#### 1. Basic Error Handling in API Calls

```javascript
import api from '../services/api';
import { getErrorMessage } from '../utils/errorHandler';

try {
  const response = await api.post('/auth/register-manager/', formData);
  // Handle success
} catch (error) {
  // Error is automatically structured by the API interceptor
  const userMessage = getErrorMessage(error);
  setError(userMessage);
}
```

#### 2. Advanced Error Handling with Custom Actions

```javascript
import { createAPIErrorHandler } from '../services/api';

const errorHandler = createAPIErrorHandler(
  (notification) => {
    // Custom notification system
    showToast(notification.message, notification.type);
  },
  (path) => {
    // Custom navigation
    navigate(path);
  }
);

// Use in component
try {
  await authService.registerManager(email, password, name);
} catch (error) {
  await errorHandler(error, 'Manager Registration');
}
```

#### 3. Form Validation Error Handling

```javascript
const [fieldErrors, setFieldErrors] = useState({});

try {
  await authService.registerManager(email, password, name);
} catch (error) {
  if (error.type === 'VALIDATION_ERROR' && error.details.field_errors) {
    setFieldErrors(error.details.field_errors);
  } else {
    setGeneralError(getErrorMessage(error));
  }
}
```

## Error Handling Patterns

### 1. Backend API Views

```python
@api_view(['POST'])
def create_resource(request):
    # Validate input
    if not request.data.get('required_field'):
        return create_validation_error_response(
            "Required field is missing",
            {"required_field": "This field is required"}
        )
    
    try:
        # Business logic
        resource = create_resource(request.data)
        return create_created_response("Resource created successfully", {"resource": resource_data})
    except IntegrityError as e:
        api_error = handle_database_error(e, "resource creation")
        return Response({
            "error": api_error.message,
            "error_code": api_error.error_code,
            "details": api_error.details
        }, status=api_error.status_code)
    except Exception as e:
        return create_internal_error_response(
            "Failed to create resource. Please try again later.",
            {"original_error": str(e)}
        )
```

### 2. Frontend Components

```jsx
const MyComponent = () => {
  const [errors, setErrors] = useState({});
  const [fieldErrors, setFieldErrors] = useState({});
  
  const handleSubmit = async (formData) => {
    try {
      await apiService.createResource(formData);
      // Handle success
    } catch (error) {
      if (error.type === 'VALIDATION_ERROR' && error.details.field_errors) {
        setFieldErrors(error.details.field_errors);
      } else {
        setErrors({ general: getErrorMessage(error) });
      }
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields with error display */}
      {fieldErrors.field_name && (
        <p className="error">{fieldErrors.field_name}</p>
      )}
      {errors.general && (
        <div className="error">{errors.general}</div>
      )}
    </form>
  );
};
```

## Testing Error Handling

### Backend Testing

```python
def test_duplicate_email_error():
    # Create a user first
    User.objects.create_user(email='test@example.com', password='password')
    
    # Try to create another user with same email
    response = client.post('/api/auth/register-manager/', {
        'email': 'test@example.com',
        'password': 'password',
        'name': 'Test User'
    })
    
    assert response.status_code == 409
    assert response.json()['error_code'] == 'CONFLICT'
    assert 'email already exists' in response.json()['error']
```

### Frontend Testing

```javascript
// Test error handling in components
test('displays validation error for missing email', async () => {
  const mockError = {
    type: 'VALIDATION_ERROR',
    message: 'Email is required',
    details: { field_errors: { email: 'This field is required' } }
  };
  
  jest.spyOn(authService, 'registerManager').mockRejectedValue(mockError);
  
  render(<ManagerRegistrationForm />);
  
  fireEvent.click(screen.getByText('Register Manager'));
  
  await waitFor(() => {
    expect(screen.getByText('This field is required')).toBeInTheDocument();
  });
});
```

## Best Practices

### Backend

1. **Always use the error handling utilities** instead of manual Response objects
2. **Provide specific error messages** that help users understand what went wrong
3. **Include relevant details** in the error response for debugging
4. **Handle database errors gracefully** using `handle_database_error()`
5. **Log errors appropriately** for monitoring and debugging

### Frontend

1. **Use the error handler utilities** for consistent error processing
2. **Display field-specific errors** for validation issues
3. **Show general errors** for non-validation issues
4. **Provide user actions** (retry, contact support) when appropriate
5. **Log errors** for debugging while showing user-friendly messages

### Error Message Guidelines

1. **Be specific and actionable**: "Email is required" vs "Invalid input"
2. **Use consistent language**: Always use the same terms for the same concepts
3. **Avoid technical jargon**: Use terms users understand
4. **Provide context**: Explain what the user needs to do to fix the error
5. **Be helpful**: Suggest solutions when possible

## Migration Guide

### Updating Existing API Views

1. Import the error handling utilities:
```python
from hirethon_template.utils.error_handling import (
    create_validation_error_response,
    create_conflict_error_response,
    # ... other utilities
)
```

2. Replace manual error responses:
```python
# Old way
return Response({"error": "User already exists"}, status=400)

# New way
return create_conflict_error_response(
    "A user with this email already exists",
    {"field": "email", "value": email}
)
```

3. Wrap business logic in try-catch blocks:
```python
try:
    # Business logic
    result = perform_operation()
    return create_success_response("Operation successful", {"data": result})
except (IntegrityError, ValidationError) as e:
    api_error = handle_database_error(e, "operation name")
    return Response({
        "error": api_error.message,
        "error_code": api_error.error_code,
        "details": api_error.details
    }, status=api_error.status_code)
```

### Updating Frontend Components

1. Import error handling utilities:
```javascript
import { getErrorMessage, ERROR_TYPES } from '../utils/errorHandler';
```

2. Update error handling in API calls:
```javascript
// Old way
catch (error) {
  const message = error.response?.data?.error || 'Something went wrong';
  setError(message);
}

// New way
catch (error) {
  const message = getErrorMessage(error);
  setError(message);
}
```

3. Handle different error types appropriately:
```javascript
catch (error) {
  if (error.type === ERROR_TYPES.VALIDATION_ERROR) {
    setFieldErrors(error.details.field_errors || {});
  } else {
    setGeneralError(getErrorMessage(error));
  }
}
```

## Monitoring and Debugging

### Backend Logging

Errors are automatically logged with structured data:
```python
# Error logging includes context and details
logger.error("API Error", extra={
    "context": "manager registration",
    "error_type": "CONFLICT",
    "user_email": email,
    "details": error_details
})
```

### Frontend Logging

Errors are logged with context for debugging:
```javascript
// Automatic logging in development
console.error('API Error:', {
  context: 'Manager Registration',
  error: {
    type: error.type,
    message: error.message,
    details: error.details
  }
});
```

This comprehensive error handling system ensures that users receive clear, actionable error messages while providing developers with the information needed to debug and improve the application.
