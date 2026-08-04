# Validação E2E — SysON + ReqValLive + MQTT (casa)

**Data casa:** 2026-07-30 · **Data lab:** 2026-08 (repetido com sucesso)  
**Demo ao orientador:** 2026-08-03 — aceite (ciclo possível)  
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
2. ~~Endurecer o contrato multi-RQ~~ (**feito** — demo na reunião 2026-08-03)
3. **Próxima reunião** — ver `docs/REUNIAO_2026-08-03_ORIENTADOR.md`: Jefferson/GSE · esqueleto de capítulos · UI EN + MQTT online (RPS)
4. Metadados de missão / snapshot SC no laudo (encaixa na escrita + UI)
5. TWC REST / plugin Magic — paralelo, não bloqueante

Ver também: `docs/RODAR_EM_CASA.md`, `deploy/syson/README.md`, `CHANGELOG.md` (§ Validated).
