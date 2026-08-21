class AppError(Exception):
    def __init__(self, detail: str, status_code: int = 400, code: str = "request_failed"):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.code = code