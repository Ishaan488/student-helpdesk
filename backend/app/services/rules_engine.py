from typing import List
from uuid import UUID

from app.models.eligibility import EligibilityRule
from app.models.student import Student
from app.schemas.eligibility import EligibilityEvaluationResult


class RulesEngine:
    """
    Deterministic rules engine for placement eligibility.
    
    Architectural rule:
    'Use deterministic systems for truth, retrieval systems for knowledge, 
     and LLMs for language and reasoning. Rules Engine decides, LLM explains.'
    """

    @staticmethod
    def evaluate(
        student: Student,
        rule: EligibilityRule,
        drive_id: UUID
    ) -> EligibilityEvaluationResult:
        """
        Evaluates a student against a drive's deterministic eligibility criteria.
        Returns a structured result with boolean eligibility and human-readable reasons.
        """
        failure_reasons: List[str] = []

        # 1. CGPA Check
        if student.cgpa < rule.minimum_cgpa:
            failure_reasons.append(
                f"CGPA {student.cgpa:.2f} is below the minimum required CGPA of {rule.minimum_cgpa:.2f}."
            )

        # 2. Backlogs Check
        if student.active_backlogs > rule.maximum_active_backlogs:
            failure_reasons.append(
                f"Active backlogs ({student.active_backlogs}) exceed the maximum allowed ({rule.maximum_active_backlogs})."
            )

        # 3. Branch Check
        if rule.allowed_branches and student.branch not in rule.allowed_branches:
            allowed_branches_str = ", ".join(rule.allowed_branches)
            failure_reasons.append(
                f"Branch '{student.branch}' is not eligible. Allowed branches: [{allowed_branches_str}]."
            )

        is_eligible = len(failure_reasons) == 0
        reasons = failure_reasons if not is_eligible else ["Student satisfies all eligibility criteria."]

        return EligibilityEvaluationResult(
            student_id=student.id,
            drive_id=drive_id,
            is_eligible=is_eligible,
            reasons=reasons,
        )


evaluate_eligibility = RulesEngine.evaluate
