# ⚠️ Dependência obrigatória: Sim_Req_Validator

**Lembrete (casa → trabalho):** este repositório **não inclui** o pacote `simreqvalidator`.
Sem ele, o ReqValLive **não instala / não corre** (schema Vampire: `RequirementRecord`,
`SuccessCriteria`, `SchemaValidator`, etc.).

## O que fazer no PC do trabalho

1. Colocar (ou clonar) o projeto **`Sim_Req_Validator`** como pasta **irmã** de `reqvallive`:

```text
Dissertacao/
├── reqvallive/           ← este repo
└── Sim_Req_Validator/    ← OBRIGATÓRIO (não vem neste git)
    ├── pyproject.toml
    └── src/simreqvalidator/...
```

2. Instalar **nessa ordem**:

```powershell
cd reqvallive
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ..\Sim_Req_Validator
pip install -e ".[dev]"
copy .env.example .env
# preencher MQTT_PASSWORD e LLM_API_KEY no .env
reqvallive
```

## Por que não está neste repo?

O `Sim_Req_Validator` é um pacote/schema separado (Vampire). O `pyproject.toml` do ReqValLive
declara `simreqvalidator>=0.1.0`, mas o código-fonte vive noutro diretório — tipicamente
desenvolvido no lab CONCEPTIO / máquina de trabalho.

## Como confirmar que está ok

```powershell
python -c "import simreqvalidator; print(simreqvalidator.__file__)"
```

Se der `ModuleNotFoundError`, a pasta irmã ainda não está instalada.
