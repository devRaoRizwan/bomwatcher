class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class BadRequestError(AppError):
    status_code = 400


class AuthenticationError(AppError):
    status_code = 401


class PermissionDeniedError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class PlanLimitError(AppError):
    status_code = 402


class TooManyRequestsError(AppError):
    status_code = 429

    def __init__(self, retry_after: int):
        super().__init__("Too many requests. Try again shortly.")
        self.retry_after = retry_after


class ServiceUnavailableError(AppError):
    status_code = 503


class UpstreamError(AppError):
    status_code = 502
