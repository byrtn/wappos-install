# Auteur : Patrick Ritaine

from __future__ import annotations


class WapposApiError(Exception):

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UpstreamUnavailableError(WapposApiError):

    status_code = 502
    code = "upstream_unavailable"


class InvalidCredentialsError(WapposApiError):

    status_code = 401
    code = "invalid_credentials"


class UpstreamProtocolError(WapposApiError):

    status_code = 502
    code = "upstream_protocol_error"


class UpstreamValidationError(WapposApiError):

    status_code = 400

    def __init__(self, message: str, error_key: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.code = error_key
        self.detail = detail
