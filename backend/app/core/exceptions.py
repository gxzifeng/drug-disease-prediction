"""Custom exception classes for consistent error handling."""
from typing import Any, Dict, Optional, List
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with consistent error format."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        self.error_code = error_code or f"ERR_{status_code}"
        self.errors = errors
        super().__init__(status_code=status_code, detail=message)


class NotFoundError(AppException):
    """Resource not found error."""
    
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier is not None:
            message = f"{resource} with ID {identifier} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="NOT_FOUND",
        )


class ValidationError(AppException):
    """Data validation error."""
    
    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VALIDATION_ERROR",
            errors=errors,
        )


class AuthenticationError(AppException):
    """Authentication failed error."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTH_FAILED",
        )


class AuthorizationError(AppException):
    """Authorization/permission error."""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="PERMISSION_DENIED",
        )


class ConflictError(AppException):
    """Resource conflict error (e.g., duplicate)."""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="CONFLICT",
        )


class BadRequestError(AppException):
    """Bad request error."""
    
    def __init__(self, message: str = "Bad request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code="BAD_REQUEST",
        )


class FileTooLargeError(AppException):
    """File size exceeds limit."""
    
    def __init__(self, max_size_mb: float):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            message=f"File too large. Maximum size is {max_size_mb}MB",
            error_code="FILE_TOO_LARGE",
        )


class UnsupportedFileTypeError(AppException):
    """Unsupported file type error."""
    
    def __init__(self, allowed_types: List[str]):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            message=f"Unsupported file type. Allowed: {', '.join(allowed_types)}",
            error_code="UNSUPPORTED_FILE_TYPE",
        )


class ServiceUnavailableError(AppException):
    """External service unavailable error."""
    
    def __init__(self, service: str = "External service"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"{service} is temporarily unavailable",
            error_code="SERVICE_UNAVAILABLE",
        )


class TaskNotFoundError(AppException):
    """Celery task not found error."""
    
    def __init__(self, task_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Task {task_id} not found",
            error_code="TASK_NOT_FOUND",
        )


class TaskFailedError(AppException):
    """Task execution failed error."""
    
    def __init__(self, task_id: str, reason: str = "Unknown error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Task {task_id} failed: {reason}",
            error_code="TASK_FAILED",
        )


class ModelNotReadyError(AppException):
    """Model is not ready for prediction."""
    
    def __init__(self, model_id: int = None, reason: str = "Model training not completed"):
        message = reason
        if model_id:
            message = f"Model {model_id}: {reason}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code="MODEL_NOT_READY",
        )


class EmbeddingNotFoundError(AppException):
    """Embedding for node not found."""
    
    def __init__(self, node_id: str, node_type: str = "node"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Embedding not found for {node_type}: {node_id}",
            error_code="EMBEDDING_NOT_FOUND",
        )
