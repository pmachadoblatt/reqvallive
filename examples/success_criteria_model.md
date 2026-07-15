# Modelo de Success Criteria — SIS-08 Methods / MSFC-HDBK-3173

Use este padrão no Markdown do ReqValLive. O **gate** aprova (ACCEPT) ou
recusa (REJECT) o critério **antes** da medição MQTT.

## Ciclo (aula)

1. Definir Success Criteria (8 dimensões)
2. Submeter para aprovação → no app: gate ACCEPT/REJECT
3. Manter o critério aprovado associado à sessão/relatório
4. Executar V&V (coletar telemetria → ok/nok)

## As 8 considerações MSFC

| Dimensão | Pergunta |
|----------|----------|
| Performance criteria | O que medir e qual o limiar? |
| Environment Test Limits | Em que condições vale a medição? |
| Tolerances | Que folga é aceitável? |
| Margins | Há margem além do limiar nominal? |
| Specifications | Ligação a CONOPS / especificação? |
| Restrictions | Escopo, pré-condições, entidades? |
| Checkpoints | Pontos de verificação no tempo/cenário? |
| Effectiveness and localization | Nível (missão/sistema/…) e alvo (drone vs global)? |

## Method × Success (coerência)

- **test** → limiar numérico com dados instrumentados (MQTT live) ✅
- **demonstration** → pass/fail sem data gathering denso (fora do MVP live)
- **inspection / analysis / …** → não são evidência por telemetria contínua

---

## Exemplo pronto a colar

```markdown
# Requisitos de missão (modelo)

## RQ-BAT-001 — Bateria mínima (system / test)
O sistema deve manter **batteryLevel >= 20 percent** em **cada drone**
durante a operação (scope: all_entities).

- Success Criteria (Performance): threshold metric=batteryLevel operator=>= value=20 unit=percent tolerance=0
- Environment: voo outdoor; telemetria MQTT activa
- Restrictions / localization: all_entities (por aeronave)
- Specifications: conops_ref CONOPS-UTM §4.2; vv_method=test
- Checkpoints: amostragem contínua enquanto measuring=true

## RQ-SEP-001 — Separação mínima (system / test)
Separação Haversine entre quaisquer dois drones:
**min_separation_m >= 20 meters** (métrica global).

- Success Criteria: threshold metric=min_separation_m operator=>= value=20 unit=meters scope=all_entities
- Pré-condição: ≥2 drones com GPS
```
