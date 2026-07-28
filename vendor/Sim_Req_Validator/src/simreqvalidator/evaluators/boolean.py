from typing import Any
from ..schema.requirement import RequirementRecord
from ..schema.success_criteria import BooleanCriteria
from .base import BaseEvaluator, ValidationContext, EvaluationResult

class BooleanEvaluator(BaseEvaluator):
    
    def evaluate(self, context: ValidationContext, requirement: RequirementRecord) -> EvaluationResult:
        if not isinstance(requirement.success_criteria, BooleanCriteria):
            raise ValueError(f"Requirement {requirement.req_id} does not have a BooleanCriteria")
        
        sc = requirement.success_criteria
        metric_name = sc.metric
        target_value = sc.expected
        
        timeseries = context.extract_metric(metric_name)
        if not timeseries:
            return EvaluationResult(
                req_id=requirement.req_id,
                passed=False,
                details=f"Metric {metric_name} is empty or missing."
            )
            
        for t, val in timeseries:
            # We assume val is float/int, mapping 1.0 to True, 0.0 to False
            bool_val = bool(val)
            if bool_val != target_value:
                return EvaluationResult(
                    req_id=requirement.req_id,
                    passed=False,
                    violating_time=t,
                    violating_value=float(bool_val),
                    details=f"Failed at t={t}. Observed: {bool_val} (Target: {target_value})"
                )
                
        return EvaluationResult(
            req_id=requirement.req_id,
            passed=True,
            details=f"Metric {metric_name} maintained {target_value} across all {len(timeseries)} points."
        )
