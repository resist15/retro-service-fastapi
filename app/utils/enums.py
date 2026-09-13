from enum import Enum


class ProviderType(Enum):
    GOOGLE = "google"
    NORMAL = "normal"


class UserRole(Enum):
    USER = "user"
    SUPER_USER = "super_user"


class AccountStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
