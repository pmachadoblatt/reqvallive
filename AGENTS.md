# AGENTS.md — ReqValLive

Antes de planear ou implementar qualquer coisa sobre **CATIA / Magic / SysML / UPDATE / CSV / REST**, leia:

1. **`docs/CONTEXT_OBRIGATORIO_CATIA.md`** (obrigatório)
2. `docs/CATIA_UPDATE_FORMATOS.md`
3. `docs/LEMBRETE_TWC_REST_EVOLUCAO.md`
4. `docs/PLANO_CATIA_GSE_APP.md`

## Factos que não pode “inventar”

- Ambiente real: **CATIA Magic 2026x + SysML v2** (não Requirement Table SysML v1).
- Export de entrada: **SysML v2 Textual Notation** (`.sysml`).
- Import `.sysml` de volta: **namespace separado** — não atualiza o modelo aberto.
- **Excel/CSV Sync** não é o caminho principal no v2 (pode não existir na view tabular).
- Tags `_go_to_verification` / `_verification_PASS|_FAIL` no **Documentation** são marcadores de texto, **não** UI PASS/FAIL do Magic.
- O laudo visual da medição é o **relatório HTML do ReqValLive**.
- Evolução para update automático no modelo: **REST SysML v2 no Teamwork Cloud** (lab tem Collaborate) ou plugin Open API.

## Dependência de runtime

- Pacote schema em `vendor/Sim_Req_Validator` (vem no git). Setup: `scripts/bootstrap.ps1`.
- Não assumir pasta irmã obrigatória.

## Tom

Se a proposta CATIA depender de feature v1 sem confirmar docs 2026x/SYSML2P, **pare e releia o contexto** antes de responder.
