# MQTT — aguardando confirmação do orientador

**Status:** backlog **não implementado** (2026-08-22)  
**Decisão registada em:** `docs/MQTT_PADRAO_MENSAGEM.md`

---

## O que já está feito (PoC)

- JSON único por drone (estilo DJI / lab CONCEPTIO)  
- Subscriber multi-drone com wildcard `#`  
- Simulador `scripts/publish_three_drones.py`  
- Motor live inalterado (threshold, range, statistical, **rate**, **dwell**)

---

## O que **não** implementar sem OK do orientador

| Item | Descrição |
|------|-----------|
| Prefixo `concept/...` | Confirmar árvore de tópicos no broker dele |
| Missão “espadrilha/fumaça” | Roteiro MQTT dedicado para demo online |
| Adaptador WARA-PS L1 | Heartbeat + sensores separados → estado interno `DroneState` |
| Dual reader | Blob actual **ou** tópicos L1 no mesmo ReqValLive |

---

## Perguntas para enviar ao orientador

1. Prefixo MQTT desejado: `concept/...` ou manter `conceptio/reqval`?  
2. Demo online: só simulador ou drones reais no novo formato?  
3. Prioridade: roteiro de missão no publisher **antes** do adaptador L1?  
4. Broker/host para entrega “UI + MQTT online” (item Christopher ago/2026)?

---

## Quando confirmado — ordem de implementação

1. Ajustar `publish_three_drones.py` (ou script novo) ao prefixo acordado — **sem** alterar motor SC se payload JSON igual.  
2. Documentar tópico e credenciais em `.env.example`.  
3. Só depois: adaptador L1 (heartbeat + `sensor/battery_state`, `sensor/altitude_agl`) conforme `MQTT_PADRAO_MENSAGEM.md`.

---

## Explicitamente fora de escopo deste backlog

- Plataforma WARA-PS sueca (Atlas, TST, comandos)  
- Jefferson 5–7 (eventos, frequência, estados) — depende de telemetria estruturada futura  
- Alteração do ciclo SysON → gate → laudo (já fechado)
