import operator
from typing import Any
from ..schema.requirement import RequirementRecord
from ..schema.success_criteria import ThresholdCriteria
from .base import BaseEvaluator, ValidationContext, EvaluationResult

class ThresholdEvaluator(BaseEvaluator):
    
    OPERATOR_MAP = {
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def evaluate(self, context: ValidationContext, requirement: RequirementRecord) -> EvaluationResult:
        if not isinstance(requirement.success_criteria, ThresholdCriteria):
            raise ValueError(f"Requirement {requirement.req_id} does not have a ThresholdCriteria")
        
        sc = requirement.success_criteria
        metric_name = sc.metric
        target_value = sc.value
        op_str = sc.operator
        tolerance = sc.tolerance or 0.0
        
        op_func = self.OPERATOR_MAP.get(op_str)
        if not op_func:
            return EvaluationResult(
                req_id=requirement.req_id,
                passed=False,
                details=f"Unknown operator: {op_str}"
            )
        
        timeseries = context.extract_metric(metric_name)
        if not timeseries:
            return EvaluationResult(
                req_id=requirement.req_id,
                passed=False,
                details=f"Metric {metric_name} is empty or missing."
            )
            
        for t, val in timeseries:
            # Check with tolerance.
            # If op is >=, then val + tolerance >= target_value
            # If op is <=, then val - tolerance <= target_value
            # For simplicity, we just check if it strictly passes the op with tolerance adjustment.
            
            passes = False
            if op_str == ">=":
                passes = op_func(val + tolerance, target_value)
            elif op_str == "<=":
                passes = op_func(val - tolerance, target_value)
            elif op_str == ">":
                passes = op_func(val + tolerance, target_value)
            elif op_str == "<":
                passes = op_func(val - tolerance, target_value)
            elif op_str == "==":
                passes = abs(val - target_value) <= tolerance
            elif op_str == "!=":
                passes = abs(val - target_value) > tolerance
                
            if not passes:
                return EvaluationResult(
                    req_id=requirement.req_id,
                    passed=False,
                    violating_time=t,
                    violating_value=val,
                    details=f"Failed at t={t}. Observed: {val} {sc.unit} (Target: {op_str} {target_value} {sc.unit})"
                )
                
        return EvaluationResult(
            req_id=requirement.req_id,
            passed=True,
            details=f"Metric {metric_name} maintained {op_str} {target_value} across all {len(timeseries)} points."
        )
