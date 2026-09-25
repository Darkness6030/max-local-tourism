class ServiceError(RuntimeError):
    """Ожидаемая ошибка внешней интеграции или сценария."""

    def __init__(
        self,
        service: str,
        message: str,
        *,
        status_code: int = 502,
        details: str | None = None,
    ) -> None:
        super().__init__(message)
        self.service = service
        self.message = message
        self.status_code = status_code
        self.details = details
