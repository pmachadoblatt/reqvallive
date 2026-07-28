# Especificação do Formato Canônico — SimReqValidator v1.0

> Formato padronizado para requisitos verificáveis por simulação

---

## 1. Motivação

O formato canônico do SimReqValidator resolve um problema recorrente na engenharia de sistemas: **requisitos escritos sem critérios de verificação mensuráveis**. Quando chega o momento de validar por simulação, o engenheiro precisa "inventar" as métricas e critérios, tornando o processo artesanal e não-reproduzível.

Este formato **força** que cada requisito entre na ferramenta com:
- **V&V Method** definido (Inspection, Analysis, Demonstration, Test)
- **Success Criteria** mensurável e automável

Requisitos sem estes campos são rejeitados pelo Schema Validator e classificados como **"vampiros"** — requisitos que consomem recursos sem critérios claros de completude.

## 2. Base Teórica

O formato foi derivado da síntese dos seguintes standards:

| Standard | Contribuição ao Formato |
|---|---|
| **MSFC-HDBK-3173** | Estrutura VCRM: Req ID, Text, Source, Method, Criteria, Status |
| **IEEE 29148:2018** | Atributos obrigatórios: ID, Source, Rationale, Priority, V&V Method |
| **ECSS-E-ST-10-02C** | VCD: traceability parent/child, levels/stages, close-out judgment |
| **DO-178C** | Rastreabilidade bidirecional obrigatória |
| **SIS-08 Methods** | Template: V&V Method + Success Criteria para cada requisito |

## 3. Esquema do Requisito

### 3.1 Campos Obrigatórios

| Campo | Tipo | Descrição | Exemplo |
|---|---|---|---|
| `req_id` | string | Identificador único (regex: `^[A-Za-z0-9][\w\-\.]*$`) | `"VD-SYS-001"` |
| `title` | string | Título descritivo (max 200 chars) | `"Separação mínima"` |
| `text` | string | Texto do requisito ("shall" statement, min 10 chars) | `"O sistema deve..."` |
| `rationale` | string | Justificativa / origem | `"CONOPS §3.2"` |
| `level` | enum | `mission` \| `system` \| `subsystem` \| `component` | `"system"` |
| `vv_method` | enum | Método de V&V (ver §4) | `"analysis"` |
| `success_criteria` | object | Critério mensurável (ver §5) | `{...}` |

### 3.2 Campos Opcionais

| Campo | Tipo | Default | Descrição |
|---|---|---|---|
| `conops_ref` | string | `null` | Referência ao CONOPS |
| `source` | string | `null` | Documento de origem |
| `priority` | enum | `"medium"` | `high` \| `medium` \| `low` |
| `parent_requirements` | string[] | `[]` | IDs dos requisitos-pai |
| `child_requirements` | string[] | `[]` | IDs dos requisitos-filho |
| `verification_status` | enum | `"not_started"` | Status da verificação |
| `evidence_ref` | string | `null` | Ref. à evidência |
| `tags` | string[] | `[]` | Tags para filtragem |

## 4. Métodos de V&V (VVMethod)

Baseado nos 4 métodos fundamentais do MSFC-HDBK-3173:

| Método | Valor | Automável | Quando usar |
|---|---|---|---|
| **Inspection** | `"inspection"` | ❌ | Exame visual de atributos físicos |
| **Analysis** | `"analysis"` | ✅ | Simulação, modelagem, estatística |
| **Demonstration** | `"demonstration"` | ⚠️ Parcial | Operação pass/fail observacional |
| **Test** | `"test"` | ✅ | Sob condições controladas |
| **Similarity** | `"similarity"` | ❌ | Comparação com sistema similar |
| **Review of Design** | `"review_of_design"` | ❌ | Revisão de documentos |

> **Nota:** A ferramenta executa automaticamente apenas os métodos `analysis` e `test`. Para os demais, o status é marcado como `not_applicable`.

## 5. Tipos de Success Criteria

### 5.1 Threshold

Compara métrica contra valor com operador.

```json
{
  "type": "threshold",
  "metric": "min_separation_m",
  "operator": ">=",
  "value": 20.0,
  "unit": "meters",
  "scope": "all_timesteps",
  "tolerance": 0.0
}
```

**Operadores:** `>=`, `<=`, `>`, `<`, `==`, `!=`

**Scopes:** `all_timesteps`, `all_flights`, `final_state`, `any_timestep`, `all_entities`, `per_entity`

### 5.2 Range

Valor dentro de intervalo [min, max].

```json
{
  "type": "range",
  "metric": "altitude_agl_m",
  "min_value": 30.0,
  "max_value": 400.0,
  "unit": "meters",
  "scope": "all_timesteps",
  "inclusive_min": true,
  "inclusive_max": true
}
```

### 5.3 Boolean

Condição verdadeiro/falso.

```json
{
  "type": "boolean",
  "metric": "geofence_active",
  "expected": true,
  "scope": "all_timesteps"
}
```

### 5.4 Statistical

Agregação estatística sobre série temporal.

```json
{
  "type": "statistical",
  "metric": "atfm_delay_s",
  "aggregation": "mean",
  "operator": "<",
  "value": 30.0,
  "unit": "seconds"
}
```

**Agregações:** `mean`, `median`, `max`, `min`, `std`, `percentile`, `sum`, `count`, `variance`

Para `percentile`, adicione `"percentile_value": 95.0`.

### 5.5 Temporal (MTL-inspired)

Condição com semântica temporal.

```json
{
  "type": "temporal",
  "metric": "separation_m",
  "temporal_operator": "always",
  "condition": {
    "type": "threshold",
    "metric": "separation_m",
    "operator": ">=",
    "value": 20.0,
    "unit": "meters"
  },
  "time_window": {
    "start": 0.0,
    "end": 300.0,
    "unit": "seconds"
  }
}
```

**Operadores temporais:**
- `always` (□): Condição vale em TODOS os timesteps
- `eventually` (◇): Condição vale em pelo menos UM timestep
- `never` (¬◇): Condição NÃO vale em nenhum timestep
- `until` (U): Condição A persiste até condição B ocorrer

### 5.6 Count

Contagem de ocorrências de eventos.

```json
{
  "type": "count",
  "metric": "separation_violations",
  "event_condition": {
    "type": "threshold",
    "metric": "pairwise_separation_m",
    "operator": "<",
    "value": 20.0,
    "unit": "meters"
  },
  "operator": "==",
  "value": 0
}
```

## 6. Vampire Detection

O Schema Validator classifica requisitos como "vampiros" quando o **quality score** cai abaixo de 50%. Penalidades:

| Problema | Penalidade |
|---|---|
| Termos vagos no texto | -10 por termo (max -30) |
| Método V&V não automável | -15 |
| Sem rastreabilidade (conops_ref + source) | -10 |
| Sem "deve"/"shall" statement | -15 |
| Texto muito curto (< 30 chars) | -10 |

**Termos vagos detectados (PT/EN):** adequado, suficiente, rápido, eficiente, robusto, amigável, intuitivo, fácil, simples, seguro (sem quantificação), confiável (sem MTBF), disponível (sem %)...

## 7. Formato de Arquivo

O SimReqValidator aceita requisitos em 3 formatos:

### JSON
```json
{
  "requirements": [
    { "req_id": "...", ... },
    { "req_id": "...", ... }
  ]
}
```

### YAML
```yaml
requirements:
  - req_id: "..."
    ...
```

### Requisito único
```json
{
  "req_id": "VD-SYS-001",
  "title": "...",
  ...
}
```
