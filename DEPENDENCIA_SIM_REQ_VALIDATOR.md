# Dependência: Sim_Req_Validator (`simreqvalidator`)

O schema Vampire (**RequirementRecord**, Success Criteria, gate, etc.) vive no pacote
`simreqvalidator`.

## Forma recomendada (casa / um único clone)

Este repositório **já inclui** uma cópia em:

```text
reqvallive/
└── vendor/Sim_Req_Validator/   ← vem no git
```

Instale assim:

```powershell
cd reqvallive
.\scripts\bootstrap.ps1
# ou:
pip install -e .\vendor\Sim_Req_Validator
pip install -e ".[dev]"
```

## Forma opcional (lab): pasta irmã

No laboratório ainda pode existir a pasta de desenvolvimento ao lado:

```text
Dissertacao/
├── reqvallive/
└── Sim_Req_Validator/    ← cópia de trabalho (git separado local)
```

Se preferir essa:

```powershell
pip install -e ..\Sim_Req_Validator
pip install -e ".[dev]"
```

Para o PC de casa, use sempre `vendor/` — é o que o `git pull` traz.

## Como confirmar

```powershell
python -c "import simreqvalidator; from simreqvalidator.schema.success_criteria import Aggregation; print(simreqvalidator.__file__); print(Aggregation.RANGE)"
```

Se der `ModuleNotFoundError` ou não tiver `RANGE`, rode de novo:

```powershell
pip install -e .\vendor\Sim_Req_Validator
```
