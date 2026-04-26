from enum import Enum

from fastapi import status


class ErrorCode(Enum):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code

    USER_ALREADY_EXISTS = ("User Already Exists", status.HTTP_400_BAD_REQUEST)
    INVALID_CREDENTIALS = ("Invalid Credentials", status.HTTP_401_UNAUTHORIZED)
    INTERNAL_SERVER_ERROR = (
        "Internal Error Occured!",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
