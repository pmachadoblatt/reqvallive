"""Tipos de Success Criteria para validação de requisitos por simulação.

Define os 6 tipos de critérios de sucesso mensuráveis que a ferramenta suporta.
Cada tipo mapeia para um Evaluator correspondente que executa a verificação
contra dados de simulação.

Referências:
    - MSFC-HDBK-3173: Performance criteria, tolerances, margins, specifications
    - IEEE 29148:2018: Verifiability as mandatory requirement attribute
    - MTL (Metric Temporal Logic): Temporal operators for real-time properties
    - SIS-08 Methods (Prof. Christopher): Success Criteria template

Tipos suportados:
    1. ThresholdCriteria  — Valor vs. limiar com operador (>=, <=, ==, etc.)
    2. RangeCriteria      — Valor dentro de intervalo [min, max]
    3. BooleanCriteria    — Condição verdadeiro/falso
    4. StatisticalCriteria — Agregação estatística sobre série temporal
    5. TemporalCriteria   — Condição temporal (always □, eventually ◇)
    6. CountCriteria      — Contagem de ocorrências/violações
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enumerações de apoio
# ---------------------------------------------------------------------------


class Operator(str, Enum):
    """Operadores de comparação para critérios de sucesso.

    Baseado nos operadores numéricos necessários para expressar
    performance criteria e tolerâncias (MSFC-HDBK-3173).
    """

    GTE = ">="  # Greater than or equal
    LTE = "<="  # Less than or equal
    GT = ">"    # Greater than
    LT = "<"    # Less than
    EQ = "=="   # Equal
    NEQ = "!="  # Not equal

    @property
    def symbol(self) -> str:
        """Símbolo legível para relatórios."""
        return self.value

    def evaluate(self, observed: float, expected: float) -> bool:
        """Avalia se o valor observado satisfaz o operador contra o esperado."""
        operations = {
            Operator.GTE: lambda a, b: a >= b,
            Operator.LTE: lambda a, b: a <= b,
            Operator.GT: lambda a, b: a > b,
            Operator.LT: lambda a, b: a < b,
            Operator.EQ: lambda a, b: a == b,
            Operator.NEQ: lambda a, b: a != b,
        }
        return operations[self](observed, expected)


class Scope(str, Enum):
    """Escopo de aplicação do critério de sucesso.

    Define sobre qual conjunto de dados o critério deve ser avaliado.
    """

    ALL_TIMESTEPS = "all_timesteps"  # Todos os timesteps da simulação
    ALL_FLIGHTS = "all_flights"      # Todas as aeronaves/voos
    FINAL_STATE = "final_state"      # Apenas o estado final
    ANY_TIMESTEP = "any_timestep"    # Pelo menos um timestep
    ALL_ENTITIES = "all_entities"    # Todas as entidades simuladas
    PER_ENTITY = "per_entity"        # Avaliado por entidade individual


class Aggregation(str, Enum):
    """Funções de agregação estatística.

    Usadas pelo StatisticalCriteria para calcular métricas
    agregadas sobre séries temporais de simulação.
    """

    MEAN = "mean"
    MEDIAN = "median"
    MAX = "max"
    MIN = "min"
    RANGE = "range"         # Peak-to-peak: max(série) − min(série)
    STD = "std"             # Desvio padrão
    PERCENTILE = "percentile"  # Requer percentile_value
    SUM = "sum"
    COUNT = "count"
    VARIANCE = "variance"


class TemporalOperator(str, Enum):
    """Operadores temporais inspirados em MTL (Metric Temporal Logic).

    Permitem expressar requisitos com semântica temporal:
    - ALWAYS (□): a condição deve valer em TODOS os timesteps
    - EVENTUALLY (◇): a condição deve valer em PELO MENOS UM timestep
    - NEVER: a condição não deve valer em NENHUM timestep
    - UNTIL: condição A vale até que condição B ocorra

    Referência: Pnueli, A. (1977). "The Temporal Logic of Programs."
    """

    ALWAYS = "always"        # □ (Box) — invariante global
    EVENTUALLY = "eventually"  # ◇ (Diamond) — alcançabilidade
    NEVER = "never"          # ¬◇ — complemento de eventually
    UNTIL = "until"          # U — condição persiste até outra ocorrer


# ---------------------------------------------------------------------------
# Modelos de critérios de sucesso
# ---------------------------------------------------------------------------


class ThresholdCriteria(BaseModel):
    """Critério de limiar: compara métrica contra valor com operador.

    O tipo mais comum de success criteria. Expressa condições como
    "separação mínima >= 20m" ou "atraso máximo <= 120s".

    Attributes:
        type: Literal "threshold" (discriminador para union)
        metric: Nome da métrica nos dados de simulação
        operator: Operador de comparação (>=, <=, ==, etc.)
        value: Valor de referência
        unit: Unidade de medida (informativa, não converte)
        scope: Escopo de aplicação (all_timesteps, all_flights, etc.)
        tolerance: Margem de tolerância (MSFC-HDBK-3173). Ex: ±5%

    Example:
        >>> criteria = ThresholdCriteria(
        ...     type="threshold",
        ...     metric="min_separation_m",
        ...     operator=">=",
        ...     value=20.0,
        ...     unit="meters",
        ...     scope="all_timesteps",
        ...     tolerance=0.0
        ... )
    """

    type: Literal["threshold"] = "threshold"
    metric: str = Field(
        ..., description="Nome da métrica nos dados de simulação", min_length=1
    )
    operator: Operator = Field(..., description="Operador de comparação")
    value: float = Field(..., description="Valor de referência")
    unit: str = Field(..., description="Unidade de medida")
    scope: Scope = Field(
        default=Scope.ALL_TIMESTEPS,
        description="Escopo de aplicação do critério",
    )
    tolerance: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Margem de tolerância absoluta. "
            "Ex: value=20, tolerance=0.5 → aceita [19.5, ∞) para operator >="
        ),
    )

    @property
    def effective_value(self) -> float:
        """Valor efetivo considerando a tolerância.

        Para operadores >= e >, subtrai a tolerância.
        Para operadores <= e <, soma a tolerância.
        Para == e !=, a tolerância define um intervalo.
        """
        if self.operator in (Operator.GTE, Operator.GT):
            return self.value - self.tolerance
        elif self.operator in (Operator.LTE, Operator.LT):
            return self.value + self.tolerance
        return self.value

    @property
    def human_readable(self) -> str:
        """Representação legível do critério."""
        tol = f" (±{self.tolerance}{self.unit})" if self.tolerance > 0 else ""
        return f"{self.metric} {self.operator.value} {self.value}{self.unit}{tol}"


class RangeCriteria(BaseModel):
    """Critério de intervalo: valor deve estar dentro de [min, max].

    Expressa condições como "altitude ∈ [100m, 400m]".

    Attributes:
        type: Literal "range"
        metric: Nome da métrica nos dados de simulação
        min_value: Limite inferior do intervalo
        max_value: Limite superior do intervalo
        unit: Unidade de medida
        scope: Escopo de aplicação
        inclusive_min: Se True, min_value é incluído (>=). Default: True
        inclusive_max: Se True, max_value é incluído (<=). Default: True

    Example:
        >>> criteria = RangeCriteria(
        ...     type="range",
        ...     metric="altitude_m",
        ...     min_value=100.0,
        ...     max_value=400.0,
        ...     unit="meters",
        ...     scope="all_timesteps"
        ... )
    """

    type: Literal["range"] = "range"
    metric: str = Field(..., min_length=1)
    min_value: float = Field(..., description="Limite inferior")
    max_value: float = Field(..., description="Limite superior")
    unit: str
    scope: Scope = Scope.ALL_TIMESTEPS
    inclusive_min: bool = Field(default=True, description="Incluir limite inferior")
    inclusive_max: bool = Field(default=True, description="Incluir limite superior")

    @model_validator(mode="after")
    def validate_range(self) -> "RangeCriteria":
        """Garante que min_value < max_value."""
        if self.min_value >= self.max_value:
            raise ValueError(
                f"min_value ({self.min_value}) deve ser menor que "
                f"max_value ({self.max_value})"
            )
        return self

    @property
    def human_readable(self) -> str:
        """Representação legível."""
        left = "[" if self.inclusive_min else "("
        right = "]" if self.inclusive_max else ")"
        return f"{self.metric} ∈ {left}{self.min_value}, {self.max_value}{right} {self.unit}"


class BooleanCriteria(BaseModel):
    """Critério booleano: verifica condição verdadeiro/falso.

    Expressa condições como "geofence_active == true".

    Attributes:
        type: Literal "boolean"
        metric: Nome da métrica booleana nos dados de simulação
        expected: Valor esperado (True ou False)
        scope: Escopo de aplicação

    Example:
        >>> criteria = BooleanCriteria(
        ...     type="boolean",
        ...     metric="geofence_active",
        ...     expected=True,
        ...     scope="all_timesteps"
        ... )
    """

    type: Literal["boolean"] = "boolean"
    metric: str = Field(..., min_length=1)
    expected: bool = Field(..., description="Valor booleano esperado")
    scope: Scope = Scope.ALL_TIMESTEPS

    @property
    def human_readable(self) -> str:
        """Representação legível."""
        return f"{self.metric} == {self.expected}"


class StatisticalCriteria(BaseModel):
    """Critério estatístico: aplica agregação sobre série temporal.

    Expressa condições como "mean(delay) < 30s" ou "percentile(95, latency) < 100ms".

    Attributes:
        type: Literal "statistical"
        metric: Nome da métrica nos dados de simulação
        aggregation: Função de agregação (mean, max, min, std, percentile, etc.)
        percentile_value: Valor do percentil (0-100), obrigatório se aggregation == percentile
        operator: Operador de comparação
        value: Valor de referência
        unit: Unidade de medida

    Example:
        >>> criteria = StatisticalCriteria(
        ...     type="statistical",
        ...     metric="atfm_delay_s",
        ...     aggregation="mean",
        ...     operator="<",
        ...     value=30.0,
        ...     unit="seconds"
        ... )
        >>> # Variação peak-to-peak (ReqValLive live): range(altitudeAGL) <= 1 m
        >>> # aggregation="range" → max(série) − min(série) na janela de medição
    """

    type: Literal["statistical"] = "statistical"
    metric: str = Field(..., min_length=1)
    aggregation: Aggregation
    percentile_value: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Percentil (0-100). Obrigatório se aggregation == percentile",
    )
    operator: Operator
    value: float
    unit: str

    @model_validator(mode="after")
    def validate_percentile(self) -> "StatisticalCriteria":
        """Garante que percentile_value é fornecido quando necessário."""
        if self.aggregation == Aggregation.PERCENTILE and self.percentile_value is None:
            raise ValueError(
                "percentile_value é obrigatório quando aggregation == 'percentile'"
            )
        if self.aggregation != Aggregation.PERCENTILE and self.percentile_value is not None:
            raise ValueError(
                "percentile_value só deve ser fornecido quando aggregation == 'percentile'"
            )
        return self

    @property
    def human_readable(self) -> str:
        """Representação legível."""
        if self.aggregation == Aggregation.PERCENTILE:
            agg = f"P{self.percentile_value:.0f}"
        else:
            agg = self.aggregation.value
        return f"{agg}({self.metric}) {self.operator.value} {self.value}{self.unit}"


class TimeWindow(BaseModel):
    """Janela temporal para critérios temporais (extensão MTL).

    Permite especificar que a condição temporal se aplica dentro de
    um intervalo de tempo, e não sobre toda a simulação.

    Example:
        >>> window = TimeWindow(start=0.0, end=300.0, unit="seconds")
    """

    start: float = Field(default=0.0, ge=0.0, description="Início da janela temporal")
    end: Optional[float] = Field(default=None, description="Fim da janela (None = até o final)")
    unit: str = Field(default="seconds", description="Unidade de tempo")

    @model_validator(mode="after")
    def validate_window(self) -> "TimeWindow":
        """Garante que start < end quando end é definido."""
        if self.end is not None and self.start >= self.end:
            raise ValueError(f"start ({self.start}) deve ser menor que end ({self.end})")
        return self


class TemporalCriteria(BaseModel):
    """Critério temporal: condição com semântica temporal (MTL-inspired).

    Expressa condições como:
    - □(separation > 20m) — separação SEMPRE > 20m
    - ◇(landing == true) — pouso EVENTUALMENTE ocorre
    - ¬◇(collision == true) — colisão NUNCA ocorre

    Suporta janela temporal (MTL extension):
    - □[0,300s](separation > 20m) — nos primeiros 300s, separação > 20m

    Attributes:
        type: Literal "temporal"
        metric: Nome da métrica (para referência; a condição está em 'condition')
        temporal_operator: Operador temporal (always, eventually, never, until)
        condition: Condição a ser verificada (ThresholdCriteria embutido)
        time_window: Janela temporal opcional (MTL extension)

    Example:
        >>> criteria = TemporalCriteria(
        ...     type="temporal",
        ...     metric="separation_m",
        ...     temporal_operator="always",
        ...     condition=ThresholdCriteria(
        ...         metric="separation_m",
        ...         operator=">=",
        ...         value=20.0,
        ...         unit="meters"
        ...     )
        ... )

    References:
        Pnueli, A. (1977). "The Temporal Logic of Programs." FOCS.
        Leucker, M. & Schallhart, C. (2009). "A Brief Account of Runtime Verification."
    """

    type: Literal["temporal"] = "temporal"
    metric: str = Field(..., min_length=1)
    temporal_operator: TemporalOperator
    condition: ThresholdCriteria = Field(
        ..., description="Condição a ser verificada temporalmente"
    )
    time_window: Optional[TimeWindow] = Field(
        default=None, description="Janela temporal (MTL extension)"
    )

    @property
    def human_readable(self) -> str:
        """Representação legível com notação temporal."""
        symbols = {
            TemporalOperator.ALWAYS: "□",
            TemporalOperator.EVENTUALLY: "◇",
            TemporalOperator.NEVER: "¬◇",
            TemporalOperator.UNTIL: "U",
        }
        symbol = symbols[self.temporal_operator]
        cond = self.condition.human_readable

        if self.time_window:
            end = self.time_window.end or "∞"
            window = f"[{self.time_window.start},{end}{self.time_window.unit}]"
            return f"{symbol}{window}({cond})"
        return f"{symbol}({cond})"


class CountCriteria(BaseModel):
    """Critério de contagem: conta ocorrências de eventos ou violações.

    Expressa condições como "violations < 3" ou "alerts == 0".

    O event_condition define o que conta como um "evento" a ser contado.
    Por exemplo, para contar violações de separação:
    event_condition = ThresholdCriteria(metric="separation_m", operator="<", value=20.0)

    Attributes:
        type: Literal "count"
        metric: Nome descritivo (para referência)
        event_condition: Condição que define o que é contado
        operator: Operador de comparação para a contagem
        value: Número máximo/mínimo de ocorrências

    Example:
        >>> criteria = CountCriteria(
        ...     type="count",
        ...     metric="separation_violations",
        ...     event_condition=ThresholdCriteria(
        ...         metric="separation_m",
        ...         operator="<",
        ...         value=20.0,
        ...         unit="meters"
        ...     ),
        ...     operator="<=",
        ...     value=0
        ... )
    """

    type: Literal["count"] = "count"
    metric: str = Field(..., min_length=1)
    event_condition: ThresholdCriteria = Field(
        ..., description="Condição que define o que conta como 'evento'"
    )
    operator: Operator
    value: int = Field(..., ge=0, description="Valor de referência para a contagem")

    @property
    def human_readable(self) -> str:
        """Representação legível."""
        event = self.event_condition.human_readable
        return f"count({event}) {self.operator.value} {self.value}"


# ---------------------------------------------------------------------------
# Union type para Success Criteria
# ---------------------------------------------------------------------------

SuccessCriteria = Annotated[
    Union[
        ThresholdCriteria,
        RangeCriteria,
        BooleanCriteria,
        StatisticalCriteria,
        TemporalCriteria,
        CountCriteria,
    ],
    Field(discriminator="type"),
]
"""Union type que aceita qualquer um dos 6 tipos de Success Criteria.

O campo 'type' é usado como discriminador para deserialização automática
(Pydantic discriminated union). Ao carregar um JSON com type="threshold",
o Pydantic instancia automaticamente um ThresholdCriteria.
"""
