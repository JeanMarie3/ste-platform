from app.schemas.requirements import RequirementRead
from app.schemas.testcases import TestCaseRead, TestRunRead


class InMemoryStore:
    def __init__(self) -> None:
        self.requirements: dict[str, RequirementRead] = {}
        self.test_cases: dict[str, TestCaseRead] = {}
        self.test_runs: dict[str, TestRunRead] = {}


store = InMemoryStore()
