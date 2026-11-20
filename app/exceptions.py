"""Custom exception types.

Services raise these exceptions when a business rule is broken.
Services never use HTTP objects, so they never raise FastAPI's HTTPException.
Instead, main.py has an exception handler that converts every AppError into
a clean JSON response:  {"detail": "...", "code": "..."}.
"""
class AppError(Exception):
    """Base class for all our custom errors."""

    status_code = 400
    code = "BAD_REQUEST"
    default_detail = "Bad request"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class BadRequestError(AppError):
    """400 - the request is understood but breaks a rule (e.g. slot in the past)."""

    status_code = 400
    code = "BAD_REQUEST"
    default_detail = "Bad request"


class UnauthorizedError(AppError):
    """401 - not logged in / bad credentials / bad token."""

    status_code = 401
    code = "UNAUTHORIZED"
    default_detail = "Not authenticated"


class ForbiddenError(AppError):
    """403 - logged in but not allowed to do this."""

    status_code = 403
    code = "FORBIDDEN"
    default_detail = "You do not have permission to perform this action"


class NotFoundError(AppError):
    """404 - the record does not exist (or does not belong to you)."""

    status_code = 404
    code = "NOT_FOUND"
    default_detail = "Resource not found"


class ConflictError(AppError):
    """409 - the action conflicts with the current state (e.g. slot already booked)."""

    status_code = 409
    code = "CONFLICT"
    default_detail = "Conflict with the current state of the resource"


class RateLimitError(AppError):
    """429 - too many requests."""

    status_code = 429
    code = "RATE_LIMITED"
    default_detail = "Too many requests, please try again later"
