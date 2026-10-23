class YppError(Exception):
    code = "internal_error"


class PermissionDenied(YppError):
    code = "forbidden"


class NotFound(YppError):
    code = "not_found"


class ValidationFailed(YppError):
    code = "validation_error"


class DependencyUnavailable(YppError):
    code = "dependency_unavailable"
