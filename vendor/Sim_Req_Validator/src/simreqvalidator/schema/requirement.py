"""Modelo central: RequirementRecord — formato canônico do requisito verificável.

Este é o modelo de dados principal do SimReqValidator. Cada requisito
que entra na ferramenta deve estar neste formato, com V&V Method e
Success Criteria obrigatoriamente definidos.

O formato é baseado na síntese dos seguintes standards:
    - MSFC-HDBK-3173: VCRM structure (Req ID, Text, Source, Method, Criteria, Status)
    - IEEE 29148:2018: Requirement attributes (ID, Source, Rationale, Priority, Status, V&V Method)
    - ECSS-E-ST-10-02C: VCD structure (traceability to parent/child, levels/stages)
    - DO-178C: Bidirectional traceability (Req ↔ CONOPS ↔ Result)
    - SIS-08 Methods (Prof. Christopher): V&V Method + Success Criteria template

Referência do exercício SIS-08 (slide 40-41):
    1. Criar CONOPS
    2. Revisar 15 requisitos com rationale (3 Mission, 5 System, 7 Subsystem)
    3. Escrever V&V data para cada requisito (method + success criteria + DVM)
    4. "Find Vampires" — identificar requisitos sem critérios verificáveis
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, model_validator

from simreqvalidator.schema.success_criteria import SuccessCriteria
from simreqvalidator.schema.vv_method import (
    Priority,
    RequirementLevel,
    VerificationStatus,
    VVMethod,
)


class RequirementRecord(BaseModel):
    """Formato canônico para requisito verificável por simulação.

    Todo requisito deve possuir:
    - Identificação (req_id, title, text)
    - Rastreabilidade (rationale, conops_ref, source, parent/child)
    - Classificação (level, priority)
    - V&V metadata (vv_method, success_criteria) ← OBRIGATÓRIO

    Um requisito sem vv_method ou success_criteria é um "vampiro"
    e será rejeitado pelo SchemaValidator.

    Attributes:
        req_id: Identificador único (ex: VD-SYS-001)
        title: Título descritivo curto
        text: Texto completo do requisito ("shall" statement)
        rationale: Justificativa / origem no CONOPS
        level: Nível hierárquico (mission/system/subsystem/component)
        conops_ref: Referência ao CONOPS (rastreabilidade bidirecional)
        source: Documento de origem do requisito
        priority: Prioridade (high/medium/low)
        vv_method: Método de V&V (inspection/analysis/demonstration/test/...)
        success_criteria: Critério de sucesso mensurável
        parent_requirements: IDs dos requisitos-pai (rastreabilidade para cima)
        child_requirements: IDs dos requisitos-filho (rastreabilidade para baixo)
        verification_status: Status atual da verificação
        evidence_ref: Referência à evidência de verificação (relatório, dados)
        tags: Tags opcionais para agrupamento/filtragem

    Example:
        >>> req = RequirementRecord(
        ...     req_id="VD-SYS-001",
        ...     title="Separação mínima entre aeronaves",
        ...     text="O sistema deve manter separação mínima de 20m entre aeronaves",
        ...     rationale="CONOPS §3.2 - Segurança operacional",
        ...     level="system",
        ...     conops_ref="CONOPS-VD §3.2",
        ...     vv_method="analysis",
        ...     success_criteria={
        ...         "type": "threshold",
        ...         "metric": "min_separation_m",
        ...         "operator": ">=",
        ...         "value": 20.0,
        ...         "unit": "meters",
        ...         "scope": "all_timesteps"
        ...     }
        ... )
    """

    # --- Identificação ---
    req_id: str = Field(
        ...,
        min_length=1,
        pattern=r"^[A-Za-z0-9][\w\-\.]*$",
        description="Identificador único do requisito (ex: VD-SYS-001)",
    )
    title: str = Field(
        ..., min_length=1, max_length=200, description="Título descritivo curto"
    )
    text: str = Field(
        ...,
        min_length=10,
        description=(
            "Texto completo do requisito ('shall' statement). "
            "Deve ser claro, não-ambíguo e verificável (IEEE 29148)"
        ),
    )

    # --- Rastreabilidade ---
    rationale: str = Field(
        ...,
        min_length=1,
        description="Justificativa do requisito / origem no CONOPS",
    )
    conops_ref: Optional[str] = Field(
        default=None,
        description="Referência ao CONOPS (ex: 'CONOPS-VD §3.2')",
    )
    source: Optional[str] = Field(
        default=None,
        description="Documento de origem (ex: 'SRS-2024-v1.0, Section 3.2')",
    )
    parent_requirements: list[str] = Field(
        default_factory=list,
        description="IDs dos requisitos-pai (rastreabilidade para cima)",
    )
    child_requirements: list[str] = Field(
        default_factory=list,
        description="IDs dos requisitos-filho (rastreabilidade para baixo)",
    )

    # --- Classificação ---
    level: RequirementLevel = Field(
        ..., description="Nível hierárquico no PBS"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Prioridade do requisito (IEEE 29148)",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags para agrupamento/filtragem",
    )

    # --- V&V Metadata (OBRIGATÓRIO — anti-vampiro) ---
    vv_method: VVMethod = Field(
        ...,
        description=(
            "Método de V&V: inspection, analysis, demonstration, test, "
            "similarity, review_of_design (MSFC-HDBK-3173)"
        ),
    )
    success_criteria: SuccessCriteria = Field(
        ...,
        description="Critério de sucesso mensurável (6 tipos suportados)",
    )

    # --- Status ---
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.NOT_STARTED,
        description="Status atual da verificação (VCRM)",
    )
    evidence_ref: Optional[str] = Field(
        default=None,
        description="Referência à evidência (relatório, gráfico, dataset)",
    )

    # --- Validators ---
    @model_validator(mode="after")
    def validate_automatable_method(self) -> "RequirementRecord":
        """Avisa quando o método V&V não é automável por simulação.

        Métodos como Inspection e Review of Design requerem ação humana
        e não podem ser verificados automaticamente pela ferramenta.
        O status é automaticamente definido como NOT_APPLICABLE.
        """
        if not self.vv_method.is_automatable and not self.vv_method.is_partially_automatable:
            if self.verification_status == VerificationStatus.NOT_STARTED:
                object.__setattr__(self, "verification_status", VerificationStatus.NOT_APPLICABLE)
        return self

    # --- Serialização ---
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "req_id": "VD-SYS-001",
                    "title": "Separação mínima entre aeronaves",
                    "text": (
                        "O sistema deve manter separação mínima de 20m "
                        "entre aeronaves em operação simultânea"
                    ),
                    "rationale": "CONOPS §3.2 - Segurança operacional",
                    "level": "system",
                    "conops_ref": "CONOPS-VD §3.2",
                    "vv_method": "analysis",
                    "success_criteria": {
                        "type": "threshold",
                        "metric": "min_separation_m",
                        "operator": ">=",
                        "value": 20.0,
                        "unit": "meters",
                        "scope": "all_timesteps",
                        "tolerance": 0.0,
                    },
                }
            ]
        }
    }

    # --- Métodos de classe para carga de dados ---
    @classmethod
    def load_from_file(cls, path: str | Path) -> list["RequirementRecord"]:
        """Carrega requisitos de arquivo JSON ou YAML.

        O arquivo pode conter:
        - Uma lista de requisitos: [{"req_id": ..., ...}, ...]
        - Um objeto com chave "requirements": {"requirements": [...]}

        Args:
            path: Caminho para o arquivo de requisitos

        Returns:
            Lista de RequirementRecord validados

        Raises:
            FileNotFoundError: Se o arquivo não existe
            ValueError: Se o formato é inválido
            ValidationError: Se algum requisito não passa na validação
        """
        filepath = Path(path)
        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

        content = filepath.read_text(encoding="utf-8")

        if filepath.suffix in (".yml", ".yaml"):
            data = yaml.safe_load(content)
        elif filepath.suffix == ".json":
            data = json.loads(content)
        else:
            raise ValueError(
                f"Formato não suportado: {filepath.suffix}. "
                "Use .json, .yml ou .yaml"
            )

        # Aceita lista direta ou objeto com chave "requirements"
        if isinstance(data, dict):
            if "requirements" in data:
                data = data["requirements"]
            else:
                # Requisito único
                data = [data]

        if not isinstance(data, list):
            raise ValueError("O arquivo deve conter uma lista de requisitos")

        return [cls.model_validate(req) for req in data]

    @classmethod
    def export_json_schema(cls, path: str | Path | None = None) -> dict:
        """Exporta o JSON Schema do formato canônico.

        Útil para documentação e validação externa.

        Args:
            path: Se fornecido, salva o schema no arquivo

        Returns:
            Dicionário com o JSON Schema
        """
        schema = cls.model_json_schema()

        if path is not None:
            filepath = Path(path)
            filepath.write_text(
                json.dumps(schema, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return schema

    def to_dvm_row(self) -> dict:
        """Converte o requisito para uma linha da DVM (Design Verification Matrix).

        Retorna um dicionário com as colunas padrão da VCRM (MSFC-HDBK-3173):
        Req ID | Title | Level | V&V Method | Success Criteria | Status | Evidence
        """
        criteria = self.success_criteria
        criteria_str = criteria.human_readable if hasattr(criteria, "human_readable") else str(criteria)

        return {
            "req_id": self.req_id,
            "title": self.title,
            "level": self.level.value,
            "vv_method": self.vv_method.value,
            "success_criteria": criteria_str,
            "status": self.verification_status.value,
            "status_symbol": self.verification_status.symbol,
            "evidence": self.evidence_ref or "—",
            "conops_ref": self.conops_ref or "—",
        }
