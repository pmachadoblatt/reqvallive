# Arquitetura do SimReqValidator

> Ferramenta de Validação de Requisitos Baseada em Simulação

---

## 1. Visão Geral

O SimReqValidator é composto por 5 módulos principais, organizados em uma pipeline de processamento:

```
ENTRADA → SCHEMA → ENGINE → EVALUATORS → REPORTS → SAÍDA
```

```
                    ENTRADA                      PROCESSAMENTO                    SAÍDA
              ┌─────────────────┐          ┌──────────────────────┐       ┌──────────────┐
              │                 │          │                      │       │              │
  Requisitos  │  JSON / CSV /   │          │   Validation         │       │  Relatório   │
  + Success   │  YAML           │────▶     │   Engine             │──────▶│  V&V         │
  Criteria    │                 │          │                      │       │              │
              └─────────────────┘          │   ┌──────────────┐   │       │  • PASS/FAIL │
                                           │   │  Schema      │   │       │  • Métricas  │
              ┌─────────────────┐          │   │  Validator   │   │       │  • Traçab.   │
              │                 │          │   └──────────────┘   │       │              │
  Dados de    │  Simulation     │          │   ┌──────────────┐   │       └──────┬───────┘
  Simulação   │  Output Data    │────▶     │   │  Evaluators  │   │              │
              │  (JSON/CSV)     │          │   │  (6 tipos)   │   │       ┌──────▼───────┐
              └─────────────────┘          │   └──────────────┘   │       │  DVM Matrix  │
                                           │   ┌──────────────┐   │       │  (Design     │
                                           │   │  Report      │   │       │  Verification│
                                           │   │  Generator   │   │       │  Matrix)     │
                                           │   └──────────────┘   │       └──────────────┘
                                           └──────────────────────┘
```

## 2. Módulos

### 2.1 Schema (`simreqvalidator.schema`)

**Responsabilidade:** Definir e validar o formato canônico de requisitos.

| Componente | Arquivo | Função |
|---|---|---|
| `VVMethod` | `vv_method.py` | Enum dos 4+2 métodos de V&V |
| `SuccessCriteria` | `success_criteria.py` | 6 tipos de critérios (union discriminada) |
| `RequirementRecord` | `requirement.py` | Modelo central do requisito |
| `SchemaValidator` | `validator.py` | Validação + Vampire Detector |

**Padrão de design:** Pydantic v2 models com discriminated union para deserialização automática dos 6 tipos de criteria via campo `type`.

### 2.2 Evaluators (`simreqvalidator.evaluators`) — FASE B

**Responsabilidade:** Avaliar dados de simulação contra success criteria.

| Evaluator | Criteria Type | Estratégia |
|---|---|---|
| `ThresholdEvaluator` | `threshold` | Comparação direta (com tolerância) |
| `RangeEvaluator` | `range` | Verificação de intervalo |
| `BooleanEvaluator` | `boolean` | Verificação true/false |
| `StatisticalEvaluator` | `statistical` | Agregação + comparação |
| `TemporalEvaluator` | `temporal` | Varredura temporal (MTL) |
| `CountEvaluator` | `count` | Contagem de eventos |

**Padrão de design:** Strategy pattern. `EvaluatorBase` define a interface; `EvaluatorRegistry` mapeia `criteria.type` → evaluator.

### 2.3 Engine (`simreqvalidator.engine`) — FASE B

**Responsabilidade:** Orquestrar o fluxo completo de validação.

```
1. Carregar requisitos (JSON/CSV/YAML)
2. Validar schema (SchemaValidator)
3. Carregar dados de simulação
4. Para cada requisito automável:
   a. Selecionar Evaluator via criteria.type
   b. Extrair métrica dos dados
   c. Avaliar contra success criteria
   d. Registrar resultado (PASS/FAIL/WARNING)
5. Gerar relatório
```

### 2.4 Reports (`simreqvalidator.reports`) — FASE B

**Responsabilidade:** Gerar artefatos de saída.

| Formato | Descrição |
|---|---|
| DVM (Markdown/HTML) | Design Verification Matrix completa |
| Relatório por requisito | PASS/FAIL + evidências + gráficos |
| CSV | Exportação tabular |
| Rastreabilidade | Requisito ↔ CONOPS ↔ Resultado |

### 2.5 CLI (`simreqvalidator.cli`) — FASE B

**Responsabilidade:** Interface de linha de comando via Typer.

```bash
simreqvalidator validate <reqs.json> --data <sim.csv>
simreqvalidator check <reqs.json>          # Vampire detector
simreqvalidator dvm <reqs.json> --format html
simreqvalidator schema --export schema.json
```

## 3. Integração com ADS Arena

O SimReqValidator pode ser deployado como plugin do ADS Arena:

```
arena-plugin/
├── backend/
│   ├── plugin.json     # Manifesto (id: sim_req_validator)
│   ├── plugin.py       # PluginBase → importa simreqvalidator
│   ├── api.py          # Django Ninja Router (REST endpoints)
│   └── models.py       # ValidationRun, RequirementSet
└── frontend/           # React UI (FASE C)
```

O plugin é uma **camada fina** — todo o core fica no pacote Python standalone.

## 4. Stack Tecnológico

| Componente | Tecnologia | Justificativa |
|---|---|---|
| **Models** | Pydantic v2 | Validação robusta, JSON Schema nativo |
| **Data** | Pandas / NumPy | Manipulação de séries temporais |
| **Charts** | Matplotlib | Gráficos de evidência |
| **CLI** | Typer + Rich | UX moderna no terminal |
| **Tests** | pytest | Framework padrão |
| **Lint** | ruff + mypy | Qualidade de código |
| **Arena** | Django Ninja | API REST para plugin |

## 5. Decisões de Design

### Por que Pydantic v2?
- Discriminated unions nativas (campo `type` seleciona o modelo automaticamente)
- JSON Schema gerado automaticamente (contribuição acadêmica)
- Validação robusta com mensagens de erro claras
- Performance 5-50x melhor que v1

### Por que separar core e plugin?
- Core funciona standalone (pip install, CLI, script Python)
- Plugin é opcional — só necessário quando deployado na Arena
- Facilita testes unitários (sem dependência de Django)
- Repositório único, instalação modular via extras (`pip install .[arena]`)

### Por que não LTL/MTL formal completo?
- Orientador indicou: simplificar para critérios mensuráveis
- MTL completo = escopo maior que mestrado
- O TemporalCriteria é **inspirado** em MTL (operadores □, ◇) mas não implementa model checking formal
- Trabalho futuro: integração com verificadores formais
