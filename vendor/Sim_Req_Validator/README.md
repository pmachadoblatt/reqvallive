# SimReqValidator

**Ferramenta de Validação de Requisitos Baseada em Simulação**
*Extensão do CONCEPTIO Systems Engineering Framework*

---

## Visão Geral

O SimReqValidator é uma ferramenta Python que automatiza a verificação de requisitos de engenharia de sistemas contra dados de simulação, utilizando critérios de sucesso (Success Criteria) pré-definidos.

### O Problema

Requisitos são frequentemente escritos de forma **não-verificável** — sem critérios de sucesso, sem método de verificação definido, e sem rastreabilidade ao CONOPS. Quando chega o momento de validar por simulação, o engenheiro precisa "inventar" as métricas e critérios, tornando o processo artesanal e não-reproduzível.

### A Solução

Uma ferramenta que:
1. **Exige** que cada requisito entre com seus critérios de validação pré-definidos (V&V Method + Success Criteria)
2. **Classifica** o método de verificação adequado (Inspeção, Análise, Demonstração, Teste — MSFC-HDBK-3173)
3. **Executa** automaticamente a verificação por simulação contra os critérios de sucesso definidos
4. **Gera** relatórios com rastreabilidade bidirecional (Requisito ↔ CONOPS ↔ Resultado)

## Base Teórica

| Standard | Contribuição |
|---|---|
| MSFC-HDBK-3173 | Métodos IADT, VCRM, success criteria guidelines |
| IEEE 29148:2018 | Atributos de requisitos, verificabilidade |
| IEEE 1012:2016 | Integrity levels, V&V escalável |
| ECSS-E-ST-10-02C | VCD como documento vivo, verificação hierárquica |
| DO-178C/DO-331 | Requirements-based testing, rastreabilidade bidirecional |

## Instalação

```bash
pip install -e .
```

## Uso Rápido

```bash
# Validar requisitos contra dados de simulação
simreqvalidator validate requirements.json --data simulation_output.csv

# Detectar requisitos "vampiros" (sem critérios verificáveis)
simreqvalidator check requirements.json

# Gerar Design Verification Matrix (DVM)
simreqvalidator dvm requirements.json --format html
```

## Uso como Biblioteca

```python
from simreqvalidator.schema import RequirementRecord
from simreqvalidator.engine import ValidationEngine

# Carregar requisitos
requirements = RequirementRecord.load_from_file("requirements.json")

# Executar validação
engine = ValidationEngine()
results = engine.validate(requirements, simulation_data="output.csv")

# Gerar DVM
results.to_dvm(format="markdown")
```

## Estrutura do Projeto

```
Sim_Req_Validator/
├── src/simreqvalidator/       # Pacote Python principal
│   ├── schema/                # Formato canônico (Pydantic models)
│   ├── evaluators/            # 6 evaluators (Threshold, Range, Boolean, Statistical, Temporal, Count)
│   ├── engine/                # Motor de validação
│   ├── reports/               # Geração de relatórios (DVM, HTML, Markdown, CSV)
│   └── cli/                   # Interface de linha de comando
├── tests/                     # Testes unitários
├── docs/                      # Documentação + fichamentos
├── examples/                  # Exemplos de uso
└── arena-plugin/              # Plugin para o ADS Arena
```

## Contexto Acadêmico

Este projeto é parte da dissertação de mestrado no **Instituto Tecnológico de Aeronáutica (ITA)**, dentro do **CONCEPTIO Systems Engineering Framework**.

- **Mestrando:** Pedro
- **Período:** Jun–Dez 2026
- **Orientador:** Prof. Christopher

## Licença

Proprietário — Todos os direitos reservados. Ver [LICENSE](LICENSE).
