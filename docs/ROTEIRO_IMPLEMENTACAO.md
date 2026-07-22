# Roteiro de implementação — features SE (para avaliação)

Documento de planejamento pós-`FEATURES_MESTRADO_SE.md`.  
Objetivo: escolher **o que fazemos a seguir** com esforço e dependências explícitos.

**Legenda de esforço:** S ≤ 0,5 dia · M 1–2 dias · L 3–5 dias  
**Estado:** feito / parcial / gap

---

## Princípio já decidido (motor live)

Não inventar métricas MQTT novas para cada formulação de requisito.

| Tipo SC | Semântica | Exemplo |
|---------|-----------|---------|
| `threshold` / `range` | valor **instantâneo** por amostra | `batteryLevel >= 20` |
| `statistical` + `range`/`max`/`min` | agregado na **janela de medição** sobre a **mesma** métrica MQTT | `range(altitudeAGL) <= 1` |

Isto cobre “não variar mais de X” para **qualquer** campo telemetria (altitude, bateria, velocidade…), sem `altitude_variation_m`.

---

## Fase 0 — Já entregue / consolidar (não priorizar)

| ID | Item | Estado |
|----|------|--------|
| F-SC-02/03/04, F-VV-02 | Gate + Method×Success + texto mensurável | feito |
| F-EV-03/04 | FAIL latch + evidência min/max/1ª falha | feito |
| F-EV-01/02 | MQTT multi-drone | feito |
| F-MB-01 | Esqueleto SysML | feito |
| — | Window statistical `range`/`max`/`min` | **feito agora** |

**Critério de saída:** regressão verde (`pytest`) + 1 ensaio lab com `examples/altitude_variation.json`.

---

## Fase 1 — Fechar claim P0 da dissertação (obrigatório)

Ordem sugerida; cada item é um PR pequeno.

### 1.1 Snapshot imutável do SC aprovado — **F-SC-07** · esforço **M** · **FEITO**

- Ao `/start`, grava cópia JSON do(s) requisito(s)+SC + gate na sessão (`approved_sc_snapshot`).
- Avaliação live e relatório usam a cópia aprovada (`active_requirements()`).
- API: campo `approved_sc_snapshot` / `sc_frozen` + `GET /api/sessions/{id}/approved-sc`.
- **Aceite:** mutar o requisito de trabalho após o start não altera snapshot nem o limiar da corrida.

### 1.2 Relatório de procedimento completo — **F-RP-03** (+ reforço F-RP-01/02) · **M** · **FEITO**

Secções fixas no HTML (`reports/html_report.py`):
1. Método V&V (`test`) + resultado do gate (por requisito)  
2. Broker/topic/protocolo MQTT + janela `start`/`end` + duração + entidades  
3. Snapshot SC (do 1.1)  
4. Esperado vs observado + 1ª violação / contagens  
5. Últimas amostras MQTT  

- **Depende de:** 1.1 (snapshot).
- **Aceite:** um SE externo responde só com o relatório: *o que foi exigido, medido, passou/falhou, quando*.
- Teste: `tests/test_procedure_report.py`

### 1.3 Metadados de missão — **F-GOV-01** (mínimo) · **S**

- Campos: nome da missão / projeto, nº entidades vistas, timestamps.
- Persistidos na sessão e no laudo.
- **Depende de:** 1.2 (encaixe no template).
- **Aceite:** laudo identifica a corrida sem olhar logs.

### 1.4 Disclaimer SysML na UI/export — **F-MB-02** · **S**

- Texto fixo: esqueleto MBSE, **não** simulação Magic / runtime `:=`.
- **Depende de:** nada.
- **Aceite:** export SysML e ecrã de diagrama mostram o disclaimer.

**Marco Fase 1:** PoC “fechada” para cap. experimentos CONCEPTIO + claim SE honesto.

---

## Fase 2 — Rigor SE / banca (P1 recomendado)

### 2.1 UI do passo “Critério de validação” — **F-GOV-05** / F-SC-02 UI · **M–L**

- Painel errors/warnings/sugestões por dimensão MSFC (não só JSON).
- Botão “Reavaliar” → `POST .../criteria/evaluate`.
- Edição inline do SC após REJECT (**F-REQ-04**).
- **Depende de:** Fase 1 opcional, mas melhor depois do snapshot.

### 2.2 Environment / Restrictions / Checkpoints no modelo — **F-SC-06** · **M**

- Campos opcionais no MD/JSON (ou tags estruturadas) + warnings no gate.
- **Depende de:** 2.1 para ficarem visíveis.

### 2.3 Timeline rica de violações — **F-EV-05** · **M**

- Lista `{t, drone, req_id, observed, expected}` no live + laudo.
- **Depende de:** evidência já existente (parcial).

### 2.4 Export pack — **F-RP-04** · **M**

- ZIP: HTML + MD + CSV amostras + `.sysml` + snapshot SC.
- **Depende de:** 1.1–1.2.

### 2.5 Qualidade da amostra — **F-EV-06** · **S–M**

- Contagem de mensagens, gaps > N s, drones sem amostra do metric.
- Warning no laudo se evidência fraca.

---

## Fase 3 — Extensão (P2 / SARITA) — só se sobrar tempo

| ID | Item | Esforço | Nota |
|----|------|---------|------|
| F-GOV-02 | `project_id` / lab CET-ADS | S | Preparação multi-ensaio |
| F-GOV-04 | Painel multi-projeto | L | Fora do núcleo mestrado |
| F-RP-05 | Hash do laudo | S | Credibilidade, opcional |
| — | `mean` / percentil / boolean / temporal MTL | L+ | Novo motor de agregação |
| — | Magic live / parâmetros `:=` | — | **Fora de escopo** |

---

## Matriz “o que escolher agora?”

| Se o objetivo imediato for… | Faça |
|------------------------------|------|
| Fechar dissertação / claim SE | **Fase 1 completa** (1.1 → 1.4) |
| Demo impressionante para banca | Fase 1 + **2.1** + **2.3** |
| Entrega ao projeto lab | Fase 1 + **2.4** |
| Só validar o bug da altura | Já coberto pelo statistical `range` — ensaio com `altitude_variation.json` |

---

## Checklist de decisão (para ti)

Marca o que entra no próximo sprint:

- [x] 1.1 Snapshot SC aprovado  
- [x] 1.2 Relatório de procedimento  
- [ ] 1.3 Metadados de missão  
- [ ] 1.4 Disclaimer SysML  
- [ ] 2.1 UI do gate  
- [ ] 2.2 Environment/Checkpoints  
- [ ] 2.3 Timeline de violações  
- [ ] 2.4 Export pack  
- [ ] 2.5 Qualidade da amostra  
- [ ] (P2) project_id / hash / agregações mean…

**Recomendação:** próximo sprint = **1.3 + 1.4** (fecha P0); depois UI do gate (2.1) se quiser demo de banca.
