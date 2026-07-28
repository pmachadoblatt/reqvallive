from typing import List
from pydantic import BaseModel
from ..schema.requirement import RequirementRecord
from .base import ValidationContext, EvaluationResult
from .coverage import CoverageChecker, CoverageReport
from .threshold import ThresholdEvaluator
from .boolean import BooleanEvaluator

class EngineReport(BaseModel):
    coverage: CoverageReport
    evaluations: List[EvaluationResult]
    passed_all: bool

class EvaluationEngine:
    def __init__(self):
        self.evaluators = {
            "threshold": ThresholdEvaluator(),
            "boolean": BooleanEvaluator()
            # Add range, statistical, temporal, count here later
        }
        
    def run(self, requirements: List[RequirementRecord], dataset: List[dict]) -> EngineReport:
        context = ValidationContext(timeseries=dataset)
        
        # 1. Check Coverage
        coverage = CoverageChecker.check_coverage(requirements, context)
        
        evaluations = []
        
        # 2. Evaluate
        for req in requirements:
            if req.success_criteria:
                evaluator_key = req.success_criteria.type
                evaluator = self.evaluators.get(evaluator_key)
                if evaluator:
                    result = evaluator.evaluate(context, req)
                    evaluations.append(result)
                else:
                    evaluations.append(EvaluationResult(
                        req_id=req.req_id,
                        passed=False,
                        details=f"No evaluator implemented for criteria type: {evaluator_key}"
                    ))
            else:
                evaluations.append(EvaluationResult(
                    req_id=req.req_id,
                    passed=False,
                    details="Requirement has no success criteria."
                ))
                
        passed_all = coverage.is_covered and all(e.passed for e in evaluations)
        
        return EngineReport(
            coverage=coverage,
            evaluations=evaluations,
            passed_all=passed_all
        )
