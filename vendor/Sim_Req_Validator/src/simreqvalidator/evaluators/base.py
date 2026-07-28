from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ValidationContext(BaseModel):
    """
    Represents the mathematical state of the simulation over time.
    A simple dataset containing mapped signals/metrics.
    """
    timeseries: List[Dict[str, Any]] = Field(default_factory=list)

    def extract_metric(self, metric_name: str) -> List[tuple[float, float]]:
        """
        Extracts a specific metric over time.
        Returns a list of (time, value) tuples.
        Assumes each data point has a 'time' key. If not, uses index as time.
        """
        result = []
        for i, point in enumerate(self.timeseries):
            if metric_name in point:
                t = point.get("time", float(i))
                val = point[metric_name]
                if val is not None:
                    result.append((t, float(val)))
        return result

    def get_available_metrics(self) -> set[str]:
        """Returns a set of all metric keys present in the timeseries (excluding 'time')."""
        metrics = set()
        for point in self.timeseries:
            metrics.update([k for k in point.keys() if k != "time"])
        return metrics


class EvaluationResult(BaseModel):
    """Result of evaluating a single requirement."""
    req_id: str
    passed: bool
    details: str
    violating_time: Optional[float] = None
    violating_value: Optional[float] = None


class BaseEvaluator:
    """Base class for all mathematical evaluators."""
    
    def evaluate(self, context: ValidationContext, requirement: Any) -> EvaluationResult:
        """
        Evaluates the requirement against the given simulation context.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement evaluate()")
