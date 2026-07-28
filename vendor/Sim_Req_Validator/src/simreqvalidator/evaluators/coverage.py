from typing import List, Optional
from pydantic import BaseModel
from ..schema.requirement import RequirementRecord
from .base import ValidationContext

class CoverageIssue(BaseModel):
    req_id: str
    missing_metric: str
    message: str

class CoverageReport(BaseModel):
    is_covered: bool
    issues: List[CoverageIssue]

class CoverageChecker:
    """
    Statically analyzes if the provided simulation data contains 
    the metrics required by the set of requirements.
    """
    
    @staticmethod
    def check_coverage(requirements: List[RequirementRecord], context: ValidationContext) -> CoverageReport:
        available_metrics = context.get_available_metrics()
        issues = []
        
        for req in requirements:
            sc = req.success_criteria
            if not sc or not getattr(sc, 'metric', None):
                continue
                
            required_metric = sc.metric
            if required_metric not in available_metrics:
                issues.append(
                    CoverageIssue(
                        req_id=req.req_id,
                        missing_metric=required_metric,
                        message=f"Requirement {req.req_id} requires metric '{required_metric}', which was not found in the simulation logs."
                    )
                )
                
        return CoverageReport(
            is_covered=len(issues) == 0,
            issues=issues
        )
