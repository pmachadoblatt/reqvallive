"""Configuração compartilhada dos testes."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def examples_dir() -> Path:
    """Diretório de exemplos."""
    return Path(__file__).parent.parent / "examples"


@pytest.fixture
def example_requirements_path(examples_dir: Path) -> Path:
    """Caminho para o arquivo de requisitos exemplo."""
    return examples_dir / "requirements_example.json"


@pytest.fixture
def example_requirements_data(example_requirements_path: Path) -> list[dict]:
    """Dados brutos dos requisitos exemplo."""
    with open(example_requirements_path, encoding="utf-8") as f:
        data = json.load(f)
    return data["requirements"]


@pytest.fixture
def valid_threshold_req() -> dict:
    """Requisito válido com ThresholdCriteria."""
    return {
        "req_id": "TEST-001",
        "title": "Separação mínima",
        "text": "O sistema deve manter separação mínima de 20 metros",
        "rationale": "Segurança operacional",
        "level": "system",
        "conops_ref": "CONOPS §3.2",
        "vv_method": "analysis",
        "success_criteria": {
            "type": "threshold",
            "metric": "min_separation_m",
            "operator": ">=",
            "value": 20.0,
            "unit": "meters",
            "scope": "all_timesteps",
        },
    }


@pytest.fixture
def vampire_req() -> dict:
    """Requisito vampiro — termos vagos, sem rastreabilidade."""
    return {
        "req_id": "VAMP-001",
        "title": "Interface adequada",
        "text": "A interface será intuitiva e adequada para uso eficiente",
        "rationale": "Usabilidade genérica",
        "level": "system",
        "vv_method": "inspection",
        "success_criteria": {
            "type": "boolean",
            "metric": "is_adequate",
            "expected": True,
            "scope": "final_state",
        },
    }
