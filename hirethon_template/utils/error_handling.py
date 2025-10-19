"""
Centralized error handling utilities for consistent API responses.
"""
from rest_framework import status
from rest_framework.response import Response
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from typing import Dict, Any, Optional


class APIError(Exception):
    """Base exception for API errors with user-friendly messages."""
    
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, 
                 error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundError(APIError):
    """Exception for resource not found errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details
        )


class ConflictError(APIError):
    """Exception for resource conflict errors (e.g., duplicate entries)."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details
        )


class UnauthorizedError(APIError):
    """Exception for unauthorized access errors."""
    
    def __init__(self, message: str = "Unauthorized access", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            details=details
        )


class ForbiddenError(APIError):
    """Exception for forbidden access errors."""
    
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            details=details
        )


class InternalServerError(APIError):
    """Exception for internal server errors."""
    
    def __init__(self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_ERROR",
            details=details
        )


def create_error_response(error: APIError) -> Response:
    """Create a standardized error response from an APIError."""
    response_data = {
        "error": error.message,
        "error_code": error.error_code,
    }
    
    if error.details:
        response_data["details"] = error.details
    
    return Response(response_data, status=error.status_code)


def handle_database_error(exception: Exception, context: str = "operation") -> APIError:
    """Handle database-related errors and convert them to user-friendly APIError."""
    
    if isinstance(exception, IntegrityError):
        error_message = str(exception).lower()
        
        # Handle unique constraint violations
        if "email" in error_message and ("unique" in error_message or "duplicate" in error_message):
            return ConflictError(
                message="A user with this email already exists.",
                details={"field": "email", "context": context}
            )
        elif "username" in error_message and ("unique" in error_message or "duplicate" in error_message):
            return ConflictError(
                message="A user with this username already exists.",
                details={"field": "username", "context": context}
            )
        else:
            return InternalServerError(
                message=f"Database integrity error during {context}.",
                details={"original_error": str(exception)}
            )
    
    elif isinstance(exception, ValidationError):
        return ValidationError(
            message=f"Validation error during {context}: {str(exception)}",
            details={"validation_errors": exception.message_dict if hasattr(exception, 'message_dict') else str(exception)}
        )
    
    else:
        return InternalServerError(
            message=f"Unexpected error during {context}.",
            details={"original_error": str(exception)}
        )


def create_success_response(message: str, data: Optional[Dict[str, Any]] = None, 
                          status_code: int = status.HTTP_200_OK) -> Response:
    """Create a standardized success response."""
    response_data = {
        "message": message,
    }
    
    if data:
        response_data.update(data)
    
    return Response(response_data, status=status_code)


def create_created_response(message: str, data: Optional[Dict[str, Any]] = None) -> Response:
    """Create a standardized created response (201)."""
    return create_success_response(message, data, status.HTTP_201_CREATED)


def create_validation_error_response(message: str, field_errors: Optional[Dict[str, str]] = None) -> Response:
    """Create a standardized validation error response."""
    error = ValidationError(message, {"field_errors": field_errors} if field_errors else None)
    return create_error_response(error)


def create_conflict_error_response(message: str, details: Optional[Dict[str, Any]] = None) -> Response:
    """Create a standardized conflict error response."""
    error = ConflictError(message, details)
    return create_error_response(error)


def create_not_found_error_response(message: str, details: Optional[Dict[str, Any]] = None) -> Response:
    """Create a standardized not found error response."""
    error = NotFoundError(message, details)
    return create_error_response(error)


def create_unauthorized_error_response(message: str = "Unauthorized access", 
                                     details: Optional[Dict[str, Any]] = None) -> Response:
    """Create a standardized unauthorized error response."""
    error = UnauthorizedError(message, details)
    return create_error_response(error)


def create_forbidden_error_response(message: str = "Access forbidden", 
                                  details: Optional[Dict[str, Any]] = None) -> Response:
    """Create a standardized forbidden error response."""
    error = ForbiddenError(message, details)
    return create_error_response(error)


def create_internal_error_response(message: str = "Internal server error", 
                                 details: Optional[Dict[str, Any]] = None) -> Response:
    """Create a standardized internal server error response."""
    error = InternalServerError(message, details)
    return create_error_response(error)
