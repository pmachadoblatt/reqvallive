# Validação E2E — SysON + ReqValLive + MQTT (casa)

**Data casa:** 2026-07-30 · **Data lab:** 2026-08 (repetido com sucesso)  
**Resultado:** **SUCESSO**

## O que foi demonstrado

```text
SysON (modelo RQ + SC + _go_to_verification)
    → ReqValLive (import / gate / GSE)
    → MQTT lab Conceptio (telemetria)
    → medição + laudo
    → Publicar no SysON
    → VerificationResult_* aparece / atualiza no modelo
```

Ambiente:

| Peça | Onde |
|------|------|
| SysON | Docker `localhost:8081` (`eclipsesyson/syson:v2025.6.0`) |
| ReqValLive | `http://127.0.0.1:8080` |
| MQTT | broker lab `161.24.23.15` / topic `conceptio/reqval` |

Isto fecha o ciclo que o orientador pediu **sem** runtime de simulação SysML v2 do Magic: o **anfitrião do modelo** no PoC pode ser o SysON; a **evidência live** fica no ReqValLive.

## Próximos passos (prioridade)

1. ~~Repetir no lab~~ (**feito** 2026-08)
2. **Endurecer o contrato** (`docs/SYSON_CONTRATO_DOC.md`): multi-RQ + SC `statistical`/`range` + PASS/FAIL no nome do item — *em curso* (`models/syson/reqvallive_demo.sysml`)
3. **Metadados de missão / relatório** (P0 dissertação): nome da missão, janela, snapshot SC no laudo HTML.
4. **TWC REST** (paralelo, não bloqueante): probe já existe; escrever OK/NOK no servidor quando o projeto SysML v2 no Collaborate estiver estável.
5. **Plugin Magic / CSV** só como canal secundário para quem usa CATIA desktop — não como default SysML v2.
6. **Material da dissertação:** capturas do E2E (SysON antes/depois + laudo) para o capítulo de experimentos.

Ver também: `docs/RODAR_EM_CASA.md`, `deploy/syson/README.md`, `CHANGELOG.md` (§ Validated).
