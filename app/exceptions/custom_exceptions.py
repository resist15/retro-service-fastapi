from app.exceptions.errors import ErrorCode


class RetroException(Exception):
    def __init__(
        self,
        error: ErrorCode = None,
        message: str = None,
        status_code: int = None,
    ):
        if error:
            self.error = error
            self.message = error.message
            self.status_code = error.status_code
        else:
            self.error = None
            self.message = message
            self.status_code = status_code

        super().__init__(self.message)
