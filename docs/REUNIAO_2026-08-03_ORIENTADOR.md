---
title: Reunião orientador 2026-08-03
date: 2026-08-03
tags:
  - reuniao
  - mestrado
  - syson
aliases:
  - Ata 2026-08-03
---

# Ata — reunião com o orientador (2026-08-03)

**Transcrição bruta:** [2026-08-03 16-29-31 (transcribed…).txt](./2026-08-03%2016-29-31%20(transcribed%20on%2003-Aug-2026%2017-34-00).txt)  
**Contexto:** demo ao vivo SysON ↔ ReqValLive ↔ MQTT → VerificationResult.

## Decisão principal

O ciclo duro da PoC **foi aceite como possível**:

```text
SysML (SysON) → interpretar Success Criteria → MQTT → laudo → write-back no modelo
```

O orientador: o “desespero” da dissertação (provar que dá) **está superado**. Daqui em diante: **enriquecer medição + escrever**.

Demonstrado na reunião: multi-requisito (threshold / range / statistical), gate com avisos (MSFC), GSE, MQTT, publicação no SysON (após refresh no explorador; diagrama ainda por arrastar).

## O que NÃO é bloqueio

- TWC / Collaborate / Cassandra — explicar ao suporte Dassault se útil; **não** trava o mestrado (SysON é o anfitrião da PoC).
- Aparecer automaticamente no **diagrama** SysON (hoje: explorador → arrastar) — melhoria desejável, não condição de escrita.
- Renomear “ReqValLive” — desejo estético; não é entregável da próxima reunião.

## Três entregas para a próxima reunião

Recapituladas pelo orientador (também no WhatsApp):

| # | Entrega | Notas |
|---|---------|--------|
| 1 | **Resultado da conversa com o Jefferson** | Sintra Lab / LabVIEW–GSE; naturezas de observação além de threshold/range/statistical. Rascunho: [[EMAIL_JEFFERSON_GSE]] |
| 2 | **Estrutura dos capítulos** (“esqueleto”) | Apresentar o plano de texto; template do orientador se disponível; base em [[ESCOPO_DISSERTACAO]] §12 |
| 3 | **UI + MQTT online** | UI/validador em **inglês**; limpar legado CATIA na UI; missão MQTT mais realista no broker dele (`concept/concept/#`, padrão RPS) |

Pode **começar a escrever já** — não precisa esperar o Jefferson para o esqueleto/texto.

## Backlog técnico (pós-ata)

1. E-mail ao Jefferson (apresentação já feita pelo orientador via WhatsApp).
2. Esqueleto de capítulos + início da escrita.
3. UI em inglês + higiene visual (remover/ocultar fluxo CATIA antigo da face principal).
4. Publisher de missão (ex. voo espadrilha/fumaça) no MQTT do orientador; Heartbeat + Kinematics (spec RPS).
5. Após resposta Jefferson: estender tipos de avaliação / GSE no app (“código mágico” que lê atributos → GSE).
6. (Opcional) VerificationResult também no diagrama SysON; renomear app.

## Documentos relacionados

- Contrato modelo: [[SYSON_CONTRATO_DOC]]
- Escopo da dissertação: [[ESCOPO_DISSERTACAO]]
- Validação E2E: [[VALIDACAO_E2E_SYSON_CASA]]
- Deploy SysON: `deploy/syson/README.md`
