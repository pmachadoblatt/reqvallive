"""Módulo schema — Formato canônico para requisitos verificáveis por simulação.

Este módulo define o modelo de dados central do SimReqValidator:
- RequirementRecord: modelo completo de um requisito com V&V metadata
- SuccessCriteria: 6 tipos de critérios de sucesso mensuráveis
- VVMethod: os 4+2 métodos fundamentais de V&V (IADT + Similarity + Review of Design)
- SchemaValidator: validação do formato + detecção de requisitos "vampiros"
"""

from simreqvalidator.schema.vv_method import (
    VVMethod,
    RequirementLevel,
    VerificationStatus,
    Priority,
)
from simreqvalidator.schema.success_criteria import (
    SuccessCriteria,
    ThresholdCriteria,
    RangeCriteria,
    BooleanCriteria,
    StatisticalCriteria,
    TemporalCriteria,
    CountCriteria,
    Operator,
    Scope,
    Aggregation,
    TemporalOperator,
)
from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.validator import SchemaValidator

__all__ = [
    # Core model
    "RequirementRecord",
    # V&V Methods
    "VVMethod",
    "RequirementLevel",
    "VerificationStatus",
    "Priority",
    # Success Criteria
    "SuccessCriteria",
    "ThresholdCriteria",
    "RangeCriteria",
    "BooleanCriteria",
    "StatisticalCriteria",
    "TemporalCriteria",
    "CountCriteria",
    "Operator",
    "Scope",
    "Aggregation",
    "TemporalOperator",
    # Validator
    "SchemaValidator",
]
