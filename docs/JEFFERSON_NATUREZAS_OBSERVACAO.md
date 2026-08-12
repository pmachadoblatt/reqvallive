---
title: Naturezas de observação (Jefferson / GSE)
date: 2026-08-12
tags:
  - jefferson
  - gse
  - success-criteria
  - mestrado
---

# Naturezas de observação — resposta Jefferson (2026-08)

**Fonte:** e-mail de Jefferson (Sintra Lab / LabVIEW–GSE) em resposta ao pedido do Pedro  
**Pedido original:** `docs/EMAIL_JEFFERSON_GSE.md`  
**Uso:** fundamentação do capítulo Método + backlog de extensão do motor live / atributos SysON.

## Decisão (para o mestrado)

A taxonomia **não está maluca** — é uma divisão clássica de engenharia de testes / observação em GSE.  
Para a dissertação:

| Camada | Conteúdo |
|--------|----------|
| **PoC demonstrada (obrigatória)** | Natureza **Valor** (+ agregação entre entidades) e **variação em janela** (amplitude) |
| **Contribuição metodológica** | Adoptar estas 7 naturezas como **vocabulário** do método (mesmo que só 1–2 novas sejam implementadas no código) |
| **Extensão de software** | Priorizar o que o MQTT do lab **já publica** sem inventar sensores |

## As 7 naturezas (Jefferson) ↔ ReqValLive

| # | Natureza | Ideia (Jefferson) | Exemplo drone | Estado no ReqValLive |
|---|----------|-------------------|---------------|------------------------|
| 1 | **Valor** | Magnitude vs limiar / banda | `batteryLevel ≥ 20`; altitude ∈ [20, 30] | **Feito** — `threshold`, `range` |
| 2 | **Tempo** | Duração / latência de uma condição | Desvio ≤ 500 ms após obstáculo; bateria &lt; 20% por no máximo 2 s | **Não** — só amostramos valor; FAIL latch é “alguma vez violou”, não “permaneceu N ms” |
| 3 | **Sequência de eventos** | Ordem / comportamento | Detecta → calcula rota → desvia → retoma | **Não** — exige eventos nomeados + máquina de estados |
| 4 | **Taxa de variação** | Δ / derivada (slew rate) | Descarga ≤ 2 %/min; climb ≤ 5 m/s | **Parcial / distinto** — hoje `statistical`+`aggregation=range` é **amplitude** (max−min na janela), **não** taxa dV/dt |
| 5 | **Ocorrência / ausência** | Digital 0/1 | “Perdeu link?”; flag de emergência | **Não** — telemetria actual é sobretudo numérica contínua |
| 6 | **Frequência** | Contagem em janela | ≤ N perdas de link / min | **Não** — depende de (5) + janela temporal |
| 7 | **Consistência entre estados** | Invariantes cruzados | `LANDING` ⇒ trem `DEPLOYED`; ¬(EMERGÊNCIA ∧ MISSÃO_OK) | **Não** — falta modelo de estados na telemetria / SysML runtime |

### Nota importante (4)

Não confundir na escrita nem no código:

- **Amplitude na janela** (`statistical` / `range`): “não variar mais de 1 m” → `|max−min| ≤ 1`.
- **Taxa** (Jefferson §4): “não subir mais rápido que 5 m/s” → `|Δh/Δt| ≤ 5`.

São naturezas vizinhas; na dissertação declarar ambas e dizer qual a PoC implementa.

## Mapeamento sugerido para atributos SysON (futuro)

Contrato actual (`scType`): `threshold` | `range` | `statistical`.

Extensão possível (sem quebrar o existente):

| `scType` (proposta) | Natureza Jefferson | Atributos típicos |
|---------------------|--------------------|-------------------|
| `threshold` / `range` | 1 Valor | metric, operator/value, unit, scope |
| `dwell` / `latency` | 2 Tempo | metric, condition, maxDuration_ms / maxLatency_ms |
| `sequence` | 3 Sequência | steps[] / expectedOrder |
| `rate` | 4 Taxa | metric, operator, value, unit (ex. `%/min`, `m/s`) |
| `event` | 5 Ocorrência | eventName, expectPresent \| expectAbsent |
| `frequency` | 6 Frequência | eventName, maxCount, window_s |
| `state_consistency` | 7 Estados | stateA, implies / mutex stateB |

Gate MSFC: cada novo tipo entra no checklist Method × Success antes do `/start`.

## Prioridade de implementação (realista CONCEPTIO)

Ordem sugerida **depois** das entregas da próxima reunião (esqueleto + UI EN + MQTT RPS):

1. **Taxa (`rate`)** — deriva de séries MQTT já existentes (`batteryLevel`, `altitudeAGL`); pouco hardware novo.  
2. **Tempo (`dwell`)** — “violação só conta se persistir ≥ T ms”; reutiliza limiar + relógio da sessão.  
3. **Evento / frequência** — se o payload RPS/Heartbeat expuser flags digitais.  
4. **Sequência / estados** — só com telemetria de modo de voo / FSM explícita (ou stub de simulação).

Isto alimenta a task LabFlow *“Expandir modelo de SC…”* e o ponto 5 do backlog da ata 2026-08-03.

## Uso na dissertação

- Cap. **Método:** tabela das 7 naturezas + referência ao contacto GSE (Jefferson).  
- Cap. **Implementação:** o que o ReqValLive cobre hoje (=1 + amplitude) vs roadmap.  
- Cap. **Discussão / trabalhos futuros:** 2–7 como extensão natural do “código que lê atributos → GSE”.  
- **Não** claim: PoC completa todas as naturezas.

## Agradecimento (rascunho de resposta)

Ver secção no fim de `docs/EMAIL_JEFFERSON_GSE.md`.
