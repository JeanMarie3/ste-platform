from app.domain.enums import PlatformType, ReviewStatus
from app.repositories.sqlite_store import TestCaseRepository, TestRunRepository
from app.schemas.common import new_id, utc_now
from app.schemas.requirements import RequirementRead
from app.schemas.testcases import AssertionRule, ReviewAction, TestCaseRead, TestStep
from app.services.ai_service import AIService


class TestCaseService:
    def __init__(self) -> None:
        self.repository = TestCaseRepository()
        self.test_run_repository = TestRunRepository()
        self.ai_service = AIService()

    def generate_for_requirement(self, requirement: RequirementRead, api_key: str | None = None) -> list[TestCaseRead]:
        now = utc_now()
        created_items: list[TestCaseRead] = []

        for platform in requirement.platforms:
            ai_result = self.ai_service.generate_test_case(
                requirement_title=requirement.title,
                requirement_description=requirement.description,
                business_rules=requirement.business_rules,
                platform=platform.value,
                api_key=api_key,
            )

            steps = self._to_steps(ai_result.get("steps", []))
            assertions = self._to_assertions(ai_result.get("assertions", []))
            ai_generated = bool(steps and assertions)

            if not ai_generated:
                steps, assertions = self._starter_template(platform=platform, title=requirement.title)

            title = ai_result.get("title") or f"{requirement.title} - core validation ({platform.value})"
            objective = ai_result.get("objective") or f"Validate {requirement.title} for {platform.value} platform."

            item = TestCaseRead(
                id=new_id("TC"),
                requirement_id=requirement.id,
                title=title,
                objective=objective,
                platform=platform,
                priority=requirement.priority,
                review_status=ReviewStatus.GENERATED,
                steps=steps,
                assertions=assertions,
                tags=[requirement.risk, requirement.priority, platform.value],
                metadata={
                    "business_rules": requirement.business_rules,
                    "source_requirement": requirement.title,
                    "ai_generated": ai_generated,
                },
                created_at=now,
                updated_at=now,
            )
            created_items.append(item)

        return self.repository.create_many(created_items)

    def list_test_cases(self) -> list[TestCaseRead]:
        return self.repository.list()

    def get_test_case(self, test_case_id: str) -> TestCaseRead | None:
        return self.repository.get(test_case_id)

    def review_test_case(self, test_case_id: str, action: ReviewAction) -> TestCaseRead | None:
        current = self.repository.get(test_case_id)
        if current is None:
            return None
        # Convert string to ReviewStatus enum
        try:
            review_status = ReviewStatus(action.review_status)
        except ValueError:
            return None
        updated = current.model_copy(
            update={
                "review_status": review_status,
                "updated_at": utc_now(),
                "metadata": {**current.metadata, "review_comment": action.comment},
            }
        )
        return self.repository.update(updated)

    def delete_test_case(self, test_case_id: str) -> bool:
        # Remove child runs first so deletion works even on older DBs without cascade constraints.
        self.test_run_repository.delete_by_test_case_id(test_case_id)
        return self.repository.delete(test_case_id)

    def _to_steps(self, raw_steps: list[dict]) -> list[TestStep]:
        steps: list[TestStep] = []
        for step in raw_steps:
            if not isinstance(step, dict):
                continue
            action = str(step.get("action") or "perform_step")
            target = str(step.get("target") or "n/a")
            value = step.get("value")
            steps.append(TestStep(action=action, target=target, value=str(value) if value is not None else None))
        return steps

    def _to_assertions(self, raw_assertions: list[dict]) -> list[AssertionRule]:
        assertions: list[AssertionRule] = []
        for rule in raw_assertions:
            if not isinstance(rule, dict):
                continue
            assertions.append(
                AssertionRule(
                    type=str(rule.get("type") or "manual_review_required"),
                    value=str(rule.get("value")) if rule.get("value") is not None else None,
                    target=str(rule.get("target")) if rule.get("target") is not None else None,
                )
            )
        return assertions

    def _starter_template(self, platform: PlatformType, title: str) -> tuple[list[TestStep], list[AssertionRule]]:
        if platform == PlatformType.WEB:
            return (
                [
                    TestStep(action="navigate", target="/login"),
                    TestStep(action="input", target="username_field", value="test.user@example.com"),
                    TestStep(action="input", target="password_field", value="SuperSecret123"),
                    TestStep(action="click", target="login_button"),
                    TestStep(action="validate_feature", target=title),
                ],
                [
                    AssertionRule(type="url_contains", value="/dashboard"),
                    AssertionRule(type="element_visible", target="dashboard_root"),
                ],
            )
        if platform == PlatformType.API:
            slug = title.lower().replace(" ", "-")
            return (
                [
                    TestStep(action="authenticate", target="token_endpoint"),
                    TestStep(action="request", target=f"/api/{slug}"),
                ],
                [
                    AssertionRule(type="status_code", value="200"),
                    AssertionRule(type="json_field_present", target="data"),
                ],
            )
        if platform == PlatformType.DATABASE:
            return (
                [
                    TestStep(action="connect", target="primary_database"),
                    TestStep(action="query", target="validation_query"),
                ],
                [AssertionRule(type="row_count_greater_than", value="0")],
            )
        return (
            [TestStep(action="prepare", target=platform.value)],
            [AssertionRule(type="manual_review_required", value="true")],
        )
