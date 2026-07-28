"""Schema Validator e Vampire Detector.

O SchemaValidator é responsável por:
1. Validar que requisitos estão no formato canônico
2. Detectar requisitos "vampiros" — aqueles que não possuem critérios verificáveis
3. Classificar a automatizabilidade dos requisitos
4. Gerar relatórios de qualidade do banco de requisitos

O conceito de "requisito vampiro" (requirement vampire) refere-se a
requisitos mal definidos que "sugam" tempo, orçamento e recursos do
projeto sem critérios claros de completude. São caracterizados por:
- Uso de termos vagos sem quantificação ("adequado", "rápido", "eficiente")
- Ausência de método de V&V definido
- Ausência de critérios de sucesso mensuráveis
- Impossibilidade de mapear para dados de simulação

A prevenção de vampiros é uma das contribuições centrais deste mestrado:
forçar a definição de V&V Method + Success Criteria no momento da entrada
do requisito, não depois.

Referências:
    - MSFC-HDBK-3173: Success criteria guidelines
    - IEEE 29148:2018: "Good requirement" characteristics (verifiable, unambiguous)
    - SIS-08 Methods: "Find Vampires" exercise (slide 40)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from pydantic import ValidationError

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.vv_method import VVMethod


# ---------------------------------------------------------------------------
# Termos vagos que indicam requisitos potencialmente não-verificáveis
# ---------------------------------------------------------------------------

VAGUE_TERMS_PT = [
    "adequado",
    "suficiente",
    "rápido",
    "eficiente",
    "robusto",
    "bom",
    "apropriado",
    "razoável",
    "aceitável",
    "satisfatório",
    "oportuno",
    "ágil",
    "flexível",
    "amigável",
    "intuitivo",
    "fácil",
    "simples",
    "moderno",
    "seguro",  # Sem quantificar o quão "seguro"
    "confiável",  # Sem MTBF/MTTR
    "disponível",  # Sem % de disponibilidade
    "escalável",
    "performático",
    "otimizado",
]

VAGUE_TERMS_EN = [
    "adequate",
    "sufficient",
    "fast",
    "efficient",
    "robust",
    "good",
    "appropriate",
    "reasonable",
    "acceptable",
    "satisfactory",
    "timely",
    "agile",
    "flexible",
    "user-friendly",
    "intuitive",
    "easy",
    "simple",
    "modern",
    "safe",  # Without quantified safety metric
    "reliable",  # Without MTBF/MTTR
    "available",  # Without % availability
    "scalable",
    "performant",
    "optimized",
    "suitable",
    "proper",
    "effective",
]

ALL_VAGUE_TERMS = VAGUE_TERMS_PT + VAGUE_TERMS_EN


# ---------------------------------------------------------------------------
# Severity levels para issues encontradas
# ---------------------------------------------------------------------------


class IssueSeverity(str, Enum):
    """Severidade de problemas encontrados na validação."""

    ERROR = "error"      # Requisito inválido, não pode ser processado
    WARNING = "warning"  # Requisito válido mas com problemas potenciais
    INFO = "info"        # Informação / sugestão de melhoria


# ---------------------------------------------------------------------------
# Dataclasses de resultado
# ---------------------------------------------------------------------------


@dataclass
class ValidationIssue:
    """Um problema encontrado durante a validação de um requisito.

    Attributes:
        req_id: ID do requisito afetado
        severity: Nível de severidade (error/warning/info)
        code: Código do problema (ex: VAMPIRE_NO_CRITERIA, VAGUE_TERM)
        message: Mensagem descritiva do problema
        field: Campo do requisito afetado (ex: "text", "success_criteria")
        suggestion: Sugestão de como resolver o problema
    """

    req_id: str
    severity: IssueSeverity
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None

    @property
    def symbol(self) -> str:
        """Símbolo para uso em relatórios."""
        symbols = {
            IssueSeverity.ERROR: "❌",
            IssueSeverity.WARNING: "⚠️",
            IssueSeverity.INFO: "ℹ️",
        }
        return symbols[self.severity]


@dataclass
class VampireReport:
    """Relatório de detecção de vampiros para um requisito.

    Attributes:
        req_id: ID do requisito
        is_vampire: Se True, o requisito é um "vampiro"
        vampire_reasons: Lista de razões pelas quais é vampiro
        vague_terms_found: Termos vagos encontrados no texto
        automatizable: Se True, pode ser verificado automaticamente
        quality_score: Score de qualidade (0-100)
    """

    req_id: str
    is_vampire: bool = False
    vampire_reasons: list[str] = field(default_factory=list)
    vague_terms_found: list[str] = field(default_factory=list)
    automatizable: bool = True
    quality_score: float = 100.0


@dataclass
class ValidationReport:
    """Relatório completo de validação de um conjunto de requisitos.

    Attributes:
        total_requirements: Total de requisitos analisados
        valid_count: Requisitos válidos
        invalid_count: Requisitos inválidos (erros de schema)
        vampire_count: Requisitos vampiros detectados
        automatable_count: Requisitos que podem ser verificados por simulação
        issues: Lista de todos os problemas encontrados
        vampire_reports: Relatório de vampiros por requisito
        quality_score: Score geral de qualidade (0-100)
    """

    total_requirements: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    vampire_count: int = 0
    automatable_count: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)
    vampire_reports: list[VampireReport] = field(default_factory=list)

    @property
    def quality_score(self) -> float:
        """Score geral de qualidade do banco de requisitos (0-100)."""
        if self.total_requirements == 0:
            return 0.0
        # Penaliza por vampiros e requisitos inválidos
        valid_ratio = self.valid_count / self.total_requirements
        non_vampire_ratio = (
            (self.total_requirements - self.vampire_count) / self.total_requirements
        )
        return round((valid_ratio * 0.5 + non_vampire_ratio * 0.5) * 100, 1)

    @property
    def summary(self) -> str:
        """Resumo textual do relatório."""
        lines = [
            f"📊 Relatório de Validação de Requisitos",
            f"{'=' * 45}",
            f"Total de requisitos:    {self.total_requirements}",
            f"✅ Válidos:             {self.valid_count}",
            f"❌ Inválidos:           {self.invalid_count}",
            f"🧛 Vampiros detectados: {self.vampire_count}",
            f"⚙️  Automáveis:          {self.automatable_count}",
            f"📈 Score de qualidade:  {self.quality_score}%",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# SchemaValidator
# ---------------------------------------------------------------------------


class SchemaValidator:
    """Validador de requisitos no formato canônico + detector de vampiros.

    Responsabilidades:
    1. Validar que o JSON/dict de entrada é um RequirementRecord válido
    2. Detectar termos vagos no texto do requisito
    3. Verificar automatizabilidade do método V&V
    4. Verificar rastreabilidade ao CONOPS
    5. Gerar relatório de qualidade

    Usage:
        >>> validator = SchemaValidator()
        >>> report = validator.validate_batch(requirements_data)
        >>> print(report.summary)

        >>> # Ou validar um requisito individual
        >>> issues = validator.validate_single(req_dict)

        >>> # Detectar vampiros em requisitos já validados
        >>> vampires = validator.detect_vampires(valid_requirements)
    """

    def __init__(
        self,
        *,
        vague_terms: list[str] | None = None,
        strict_traceability: bool = False,
        min_text_length: int = 10,
        warn_margin_threshold: float = 5.0,
    ):
        """Inicializa o validador.

        Args:
            vague_terms: Lista customizada de termos vagos. Se None, usa a padrão.
            strict_traceability: Se True, exige conops_ref preenchido.
            min_text_length: Comprimento mínimo do texto do requisito.
            warn_margin_threshold: Margem (%) abaixo da qual emite warning.
        """
        self.vague_terms = vague_terms or ALL_VAGUE_TERMS
        self.strict_traceability = strict_traceability
        self.min_text_length = min_text_length
        self.warn_margin_threshold = warn_margin_threshold

        # Compilar regex para termos vagos (word boundary matching)
        self._vague_patterns = [
            re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            for term in self.vague_terms
        ]

    def validate_single(self, data: dict) -> tuple[Optional[RequirementRecord], list[ValidationIssue]]:
        """Valida um único requisito (dict → RequirementRecord).

        Args:
            data: Dicionário com os dados do requisito

        Returns:
            Tupla (requisito_validado_ou_None, lista_de_issues)
        """
        issues: list[ValidationIssue] = []
        req_id = data.get("req_id", "UNKNOWN")

        # 1. Validação do schema Pydantic
        try:
            requirement = RequirementRecord.model_validate(data)
        except ValidationError as e:
            for error in e.errors():
                issues.append(
                    ValidationIssue(
                        req_id=req_id,
                        severity=IssueSeverity.ERROR,
                        code="SCHEMA_VALIDATION_ERROR",
                        message=f"{error['msg']} (campo: {'.'.join(str(l) for l in error['loc'])})",
                        field=str(error["loc"][-1]) if error["loc"] else None,
                    )
                )
            return None, issues

        # 2. Verificações adicionais (pós-schema)
        issues.extend(self._check_vague_terms(requirement))
        issues.extend(self._check_traceability(requirement))
        issues.extend(self._check_automatability(requirement))
        issues.extend(self._check_shall_statement(requirement))

        return requirement, issues

    def validate_batch(self, data_list: list[dict]) -> tuple[list[RequirementRecord], ValidationReport]:
        """Valida um lote de requisitos.

        Args:
            data_list: Lista de dicionários com dados de requisitos

        Returns:
            Tupla (requisitos_válidos, relatório_completo)
        """
        report = ValidationReport(total_requirements=len(data_list))
        valid_requirements: list[RequirementRecord] = []

        for data in data_list:
            requirement, issues = self.validate_single(data)
            report.issues.extend(issues)

            if requirement is not None:
                report.valid_count += 1
                valid_requirements.append(requirement)

                # Check automatability
                if requirement.vv_method.is_automatable:
                    report.automatable_count += 1
            else:
                report.invalid_count += 1

        # Detectar vampiros nos requisitos válidos
        for req in valid_requirements:
            vampire_report = self._check_vampire(req)
            report.vampire_reports.append(vampire_report)
            if vampire_report.is_vampire:
                report.vampire_count += 1

        return valid_requirements, report

    def detect_vampires(
        self, requirements: list[RequirementRecord]
    ) -> list[VampireReport]:
        """Detecta requisitos vampiros em uma lista já validada.

        Args:
            requirements: Lista de RequirementRecord já validados

        Returns:
            Lista de VampireReport
        """
        return [self._check_vampire(req) for req in requirements]

    def check_automatable(self, requirement: RequirementRecord) -> bool:
        """Verifica se um requisito pode ser verificado automaticamente.

        Um requisito é automável se:
        - V&V Method é Analysis ou Test
        - Success Criteria é mensurável
        - A métrica pode ser mapeada para dados de simulação
        """
        return requirement.vv_method.is_automatable

    # --- Métodos internos ---

    def _check_vague_terms(self, req: RequirementRecord) -> list[ValidationIssue]:
        """Detecta termos vagos no texto do requisito."""
        issues: list[ValidationIssue] = []
        found_terms: list[str] = []

        for pattern in self._vague_patterns:
            matches = pattern.findall(req.text)
            if matches:
                found_terms.extend(matches)

        if found_terms:
            unique_terms = list(set(t.lower() for t in found_terms))
            issues.append(
                ValidationIssue(
                    req_id=req.req_id,
                    severity=IssueSeverity.WARNING,
                    code="VAGUE_TERM_DETECTED",
                    message=(
                        f"Termos vagos detectados no texto do requisito: "
                        f"{', '.join(unique_terms)}. "
                        f"Requisitos devem ser específicos e mensuráveis (IEEE 29148)."
                    ),
                    field="text",
                    suggestion=(
                        "Substitua termos vagos por valores quantificáveis. "
                        "Ex: 'rápido' → 'tempo de resposta ≤ 500ms'"
                    ),
                )
            )
        return issues

    def _check_traceability(self, req: RequirementRecord) -> list[ValidationIssue]:
        """Verifica rastreabilidade ao CONOPS."""
        issues: list[ValidationIssue] = []

        if self.strict_traceability and not req.conops_ref:
            issues.append(
                ValidationIssue(
                    req_id=req.req_id,
                    severity=IssueSeverity.WARNING,
                    code="MISSING_CONOPS_REF",
                    message=(
                        "Requisito sem referência ao CONOPS. "
                        "Rastreabilidade bidirecional é exigida por DO-178C e ECSS."
                    ),
                    field="conops_ref",
                    suggestion="Adicione a referência ao CONOPS de onde este requisito se originou.",
                )
            )

        if not req.conops_ref and not req.source:
            issues.append(
                ValidationIssue(
                    req_id=req.req_id,
                    severity=IssueSeverity.INFO,
                    code="NO_SOURCE_TRACEABILITY",
                    message=(
                        "Requisito sem fonte rastreável (conops_ref e source vazios). "
                        "Recomenda-se indicar a origem do requisito."
                    ),
                    field="source",
                )
            )

        return issues

    def _check_automatability(self, req: RequirementRecord) -> list[ValidationIssue]:
        """Verifica se o método V&V é automável pela ferramenta."""
        issues: list[ValidationIssue] = []

        if not req.vv_method.is_automatable and not req.vv_method.is_partially_automatable:
            issues.append(
                ValidationIssue(
                    req_id=req.req_id,
                    severity=IssueSeverity.INFO,
                    code="NOT_AUTOMATABLE",
                    message=(
                        f"Método V&V '{req.vv_method.value}' não é automável por simulação. "
                        f"Este requisito requer verificação manual."
                    ),
                    field="vv_method",
                    suggestion=(
                        f"Se possível, considere se o requisito pode ser verificado por "
                        f"'analysis' (simulação) ou 'test' para automação."
                    ),
                )
            )
        elif req.vv_method.is_partially_automatable:
            issues.append(
                ValidationIssue(
                    req_id=req.req_id,
                    severity=IssueSeverity.INFO,
                    code="PARTIALLY_AUTOMATABLE",
                    message=(
                        f"Método V&V '{req.vv_method.value}' é parcialmente automável. "
                        f"Resultados da simulação podem servir como evidência, "
                        f"mas a validação final pode requerer observação humana."
                    ),
                    field="vv_method",
                )
            )

        return issues

    def _check_shall_statement(self, req: RequirementRecord) -> list[ValidationIssue]:
        """Verifica se o texto contém uma 'shall' statement (IEEE 29148)."""
        issues: list[ValidationIssue] = []

        # Verificar em português e inglês
        shall_patterns = [
            r"\bdeve\b",    # PT: "deve"
            r"\bdevem\b",   # PT: "devem"
            r"\bshall\b",   # EN: "shall"
        ]

        has_shall = any(
            re.search(pattern, req.text, re.IGNORECASE)
            for pattern in shall_patterns
        )

        if not has_shall:
            issues.append(
                ValidationIssue(
                    req_id=req.req_id,
                    severity=IssueSeverity.WARNING,
                    code="NO_SHALL_STATEMENT",
                    message=(
                        "O texto do requisito não contém 'deve'/'shall'. "
                        "Requisitos verificáveis devem usar declarações 'shall' (IEEE 29148). "
                        "Nota: 'should' indica recomendação, 'shall' indica obrigação."
                    ),
                    field="text",
                    suggestion="Reformule usando 'O sistema DEVE...' ou 'The system SHALL...'",
                )
            )

        return issues

    def _check_vampire(self, req: RequirementRecord) -> VampireReport:
        """Verifica se um requisito é um vampiro.

        Um requisito é classificado como vampiro se acumula
        problemas suficientes que comprometem sua verificabilidade.
        """
        report = VampireReport(req_id=req.req_id)
        score = 100.0

        # 1. Verificar termos vagos
        for pattern in self._vague_patterns:
            matches = pattern.findall(req.text)
            if matches:
                report.vague_terms_found.extend(matches)

        if report.vague_terms_found:
            penalty = min(len(set(report.vague_terms_found)) * 10, 30)
            score -= penalty
            report.vampire_reasons.append(
                f"Contém {len(set(report.vague_terms_found))} termo(s) vago(s): "
                f"{', '.join(set(t.lower() for t in report.vague_terms_found))}"
            )

        # 2. Verificar automatizabilidade
        if not req.vv_method.is_automatable:
            report.automatizable = False
            if not req.vv_method.is_partially_automatable:
                score -= 15
                report.vampire_reasons.append(
                    f"Método V&V '{req.vv_method.value}' não é automável por simulação"
                )

        # 3. Verificar rastreabilidade
        if not req.conops_ref and not req.source:
            score -= 10
            report.vampire_reasons.append(
                "Sem rastreabilidade (conops_ref e source vazios)"
            )

        # 4. Verificar shall statement
        shall_patterns = [r"\bdeve\b", r"\bdevem\b", r"\bshall\b"]
        has_shall = any(
            re.search(p, req.text, re.IGNORECASE)
            for p in shall_patterns
        )
        if not has_shall:
            score -= 15
            report.vampire_reasons.append(
                "Texto não contém 'deve'/'shall' statement"
            )

        # 5. Verificar texto muito curto
        if len(req.text) < 30:
            score -= 10
            report.vampire_reasons.append(
                f"Texto muito curto ({len(req.text)} caracteres). "
                "Requisitos devem ser detalhados o suficiente para serem não-ambíguos"
            )

        # Score final
        report.quality_score = max(score, 0.0)
        report.is_vampire = score <= 50.0  # 50% ou abaixo é vampiro

        return report
