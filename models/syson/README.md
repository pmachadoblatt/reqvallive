# Modelos SysON (lab ↔ casa)

Contrato completo: [`docs/SYSON_CONTRATO_DOC.md`](../../docs/SYSON_CONTRATO_DOC.md)

| No SysON | Conteúdo |
|----------|----------|
| Documentation do RQ | só `_go_to_verification` |
| Item `SuccessCriteria` (sob o requirement) | métrica, operador, valor… (authoring) |
| Item `VerificationResult_FAIL_…` | resultado da medição (escrito pelo app; nome = veredicto) |
| ReqValLive | interpreta SC; não inventa; publica VerificationResult |

## Ficheiros

- `reqvallive_demo.sysml` — exemplo completo (importar no SysON)
- `RQ_01_documentation.txt` — texto para colar no Documentation

## No teu ReqTest atual

1. Limpa o Documentation do `RQ_01` para ficar **só** `_go_to_verification`.
2. Sob `RQ_01`, cria item `SuccessCriteria` + atributos (`scType`, `metric`, `operator`, `value`, `unit`, `scope`)  
   **ou** importa `reqvallive_demo.sysml` num projeto novo e usa esse.
3. No app: Importar do SysON — o SC deve vir do modelo.
