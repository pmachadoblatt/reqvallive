---
title: Padrão de mensagem MQTT (opinião)
date: 2026-08-18
tags:
  - mqtt
  - waraps
  - padronizacao
---

# Padrão de mensagem MQTT — decisão (2026-08-18)

**Pergunta:** adoptar o modelo de mensagem WARA-PS ([api-docs.waraps.org](https://api-docs.waraps.org/#/)) só como **contrato MQTT** para distribuir no futuro, sem usar a plataforma sueca?

**Resposta:** **sim, como alvo de distribuição; não, como substituição agora.**  
O código MQTT do ReqValLive **não muda nesta decisão**. O JSON DJI/lab actual continua a ser o contrato que a PoC mede.

## Porquê não trocar já

A PoC já fecha o ciclo com o payload que o CONCEPTIO publica hoje (um JSON por drone, tópico plano). Trocar o envelope no meio da escrita / UI seria custo sem consumidor segundo. O escopo da dissertação já exclui *ser* WARA-PS; o que se quer é um **dialecto partilhável**.

## Porquê vale a pena como padrão futuro

O WARA-PS L1 (heartbeat + sensores em tópicos) resolve o problema que o SARITA / CET-ADS vai ter: vários projectos no mesmo broker, identidade no caminho do tópico, presença explícita, sensores opcionais sem um JSON-monstro por fornecedor. É um vocabulário conhecido (o orientador já o apontou) e não obriga Atlas, TST nem comandos.

Recorte que faz sentido copiar:

| Copiar | Não copiar |
|--------|------------|
| Árvore `contexto/unit/air/{real\|simulation}/<agente>/…` (no lab: prefixo `concept/…`) | Core WARA-PS, Atlas, ROS bridge |
| Heartbeat + `sensor_info` | Comandos `exec/`, TST, delegação |
| Sensores separados: `position`, `speed`, `heading`, `battery_state` | Obrigar AGL/bateria a caber só no GeoPoint mínimo |

Altitude AGL e bateria, que a dissertação mede, **não são sensores obrigatórios** na spec sueca — num dialecto CONCEPTIO ficam sensores extra nomeados (`sensor/altitude_agl`, `sensor/battery_state`).

## Perspectiva de implementação (quando for altura)

Não reescrever drones nem o motor de SC. Um **adaptador**:

1. Continua a existir o JSON gordo (lab / DJI / publisher actual).
2. Um processo pequeno republica L1 no broker do orientador.
3. O ReqValLive, mais tarde, passa a **aceitar os dois**: blob actual **ou** tópicos L1 fundidos no mesmo estado interno (`DroneState`).

O motor (threshold, range, amplitude, taxa, dwell) e o SysON não dependem do envelope.

## O que isto não decide

- Não implementa o adaptador agora.
- Não obriga o firmware dos drones reais a mudar nesta sprint.
- Não abre Jefferson 5–7 (evento/frequência/sequência) — o heartbeat ajuda *depois*, não é pré-requisito da UI.

Confirmar com o orientador, quando for a entrega MQTT: prefixo `concept/…` e nível **L1 apenas**. Ver checklist em `docs/MQTT_AGUARDANDO_ORIENTADOR.md`.
