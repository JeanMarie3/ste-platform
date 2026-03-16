from enum import Enum


class PlatformType(str, Enum):
    WEB = "web"
    API = "api"
    DATABASE = "database"
    MOBILE = "mobile"
    DESKTOP = "desktop"


class ReviewStatus(str, Enum):
    GENERATED = "generated"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_UPDATE = "needs_update"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"
    SUSPICIOUS = "suspicious"
