# Estado da Arte em Verificação Automatizada por Simulação

## Dados Bibliográficos

- **Título:** Estado da Arte em Verificação Automatizada de Requisitos por Simulação
- **Tipo:** Revisão de literatura — síntese de múltiplas fontes acadêmicas e
  industriais (2020–2024)
- **Área:** Engenharia de Sistemas — Verificação e Validação Automatizada,
  Model-Based Systems Engineering (MBSE), Digital Engineering
- **Fontes primárias:** Publicações IEEE, INCOSE, AIAA, SAE, periódicos de
  Systems Engineering e conferências de MBSE/MBD

---

## Conceitos-Chave

### Frameworks de Verificação Automatizada

A literatura recente apresenta um movimento significativo em direção à
**automação de verificação de requisitos**, impulsionado pela crescente complexidade
de sistemas e pela necessidade de reduzir custos e prazos de certificação.

Os frameworks de verificação automatizada tipicamente seguem a arquitetura:

```
┌──────────────────────────────────────────────────────────────┐
│  Modelo SysML/UML         →  Mapeamento Automático          │
│  (Requisitos + Estrutura)     (Requirements Mapping)         │
├──────────────────────────────────────────────────────────────┤
│  Ambiente de Simulação    →  Execução Automatizada           │
│  (Simulink/Modelica/Python)   (Automated Testing)            │
├──────────────────────────────────────────────────────────────┤
│  Avaliação de Resultados  →  Geração de Evidência            │
│  (Pass/Fail + Métricas)       (DVM/VCR Generation)           │
└──────────────────────────────────────────────────────────────┘
```

Estes frameworks vinculam **modelos SysML** a **ambientes de execução**
(Simulink, Modelica, Python, Julia), permitindo:

- Extração automática de requisitos verificáveis dos modelos
- Geração automática de cenários de teste a partir de modelos comportamentais
- Execução automatizada de simulações contra critérios de aceitação
- Coleta automática de resultados e geração de relatórios de conformidade

### Evolução do SysML v2

O **SysML v2** (Systems Modeling Language, versão 2) representa uma evolução
significativa em relação ao SysML v1, com implicações diretas para a verificação
automatizada:

- **Semântica formal aprimorada:** O SysML v2 introduz uma semântica mais formal
  e precisa, facilitando o raciocínio automatizado sobre modelos. Isso permite que
  ferramentas de verificação interpretem modelos de forma mais confiável e
  consistente.

- **Requisitos como elementos de primeira classe:** O SysML v2 trata requisitos
  como elementos modeláveis com propriedades formais, não apenas como texto
  anotado. Isso facilita a extração automática de critérios de verificação.

- **API padronizada:** A API padronizada do SysML v2 simplifica a integração com
  ferramentas de simulação e verificação externas.

### Abordagens de Verificação Automatizada

A literatura identifica quatro abordagens principais de verificação automatizada:

#### 1. Requirements Mapping (Mapeamento de Requisitos)

Vinculação formal entre requisitos modelados em SysML e elementos de simulação
em ambientes como Simulink ou Modelica. O mapeamento define quais sinais de
simulação correspondem a quais parâmetros de requisitos.

#### 2. Automated Testing (Teste Automatizado)

Geração automática de casos de teste a partir de **modelos comportamentais**.
Utiliza técnicas como:

- Geração baseada em modelos de estado (*model-based test generation*)
- Exploração de espaço de estados (*state space exploration*)
- Testes paramétricos automatizados (*parameterized testing*)
- Geração baseada em cobertura (*coverage-driven test generation*)

#### 3. Formal/Semi-Formal Verification (Verificação Formal/Semi-Formal)

Utilização de métodos formais para verificação de propriedades:

- **Contract-Based Design:** Definição de contratos (pré-condições, pós-condições,
  invariantes) para componentes e suas interfaces. Verificação de que os contratos
  são satisfeitos em todas as composições.

- **Property-Based Verification:** Especificação de propriedades temporais e
  lógicas que o sistema deve satisfazer. Verificação por model checking ou
  runtime verification.

#### 4. CI Integration (Integração Contínua)

Integração de verificação automatizada em **pipelines de integração contínua**
(conceito emergente de **DEMOps — Digital Engineering + DevOps**):

- Execução automática de simulações de verificação a cada commit ou merge request
- Relatórios automatizados de status de verificação
- Bloqueio de merges quando simulações falham
- Dashboard de conformidade de requisitos em tempo real

### Ferramentas do Estado da Arte

A literatura e a prática industrial referenciam as seguintes ferramentas:

| Categoria               | Ferramentas                                              |
|--------------------------|----------------------------------------------------------|
| **Modelagem SysML**      | Cameo Systems Modeler, IBM Rhapsody                     |
| **Simulação**            | MATLAB/Simulink, Modelica/OpenModelica, Python, Julia   |
| **Gestão de Requisitos** | IBM DOORS, Polarion, Jama Connect                       |
| **Pipelines Customizados** | Scripts Python/Julia, frameworks CI/CD               |

---

## Métodos de V&V

### MTL — Metric Temporal Logic

A **Metric Temporal Logic (MTL)** emerge como um formalismo particularmente
poderoso para a verificação de propriedades temporais de sistemas em tempo real:

#### Conceitos Fundamentais

- **Operadores temporais anotados com tempo:** MTL estende a lógica temporal
  clássica com restrições de tempo explícitas. Exemplos:
  - □[0,10] (φ): "φ deve ser verdadeiro em todos os instantes nos próximos 10
    segundos"
  - ◇[0,5] (φ): "φ deve ser verdadeiro em pelo menos um instante nos próximos 5
    segundos"
  - φ U[0,T] ψ: "φ deve permanecer verdadeiro até que ψ se torne verdadeiro,
    dentro de T unidades de tempo"

#### Verificação Automática de Sinais

MTL permite a **verificação automática de sinais de simulação** contra
especificações temporais:

- Um sinal de simulação é comparado com uma fórmula MTL
- O resultado é um veredito booleano (satisfaz/viola) ou um valor de robustez
- A verificação pode ser realizada offline (pós-simulação) ou online (durante a
  simulação em tempo real)

#### Runtime Verification Monitors

**Monitores de verificação em tempo de execução** avaliam propriedades MTL sobre
sinais de simulação à medida que são gerados:

- Monitoração contínua sem necessidade de armazenar todo o histórico de sinais
- Detecção imediata de violações de propriedades
- Aplicável tanto a simulações quanto a execuções em hardware real

#### Semântica Robusta (Robust Semantics)

A **semântica robusta** do MTL fornece não apenas um veredito booleano, mas uma
**medida quantitativa** de quão próximo o sinal está de violar (ou satisfazer)
a propriedade:

- **Robustez positiva:** Indica margem de segurança — quão longe o sinal está
  de violar a propriedade.
- **Robustez negativa:** Indica severidade da violação — quão longe o sinal está
  de satisfazer a propriedade.
- **Aplicação:** A robustez pode ser interpretada como **margem de design**,
  fornecendo informação quantitativa sobre a proximidade do sistema ao limite
  de operação.

#### Tradução para Autômatos Temporais

Fórmulas MTL podem ser traduzidas para **autômatos temporais** (*timed automata*),
permitindo:

- Model checking automatizado
- Geração de contraexemplos
- Análise de alcançabilidade

### Metodologias de Validação de Modelos

A literatura define métricas quantitativas para validação de modelos de simulação:

| Métrica                          | Descrição                                      |
|----------------------------------|-------------------------------------------------|
| **RMSE**                         | Root Mean Square Error — erro quadrático médio  |
| **MAPE**                         | Mean Absolute Percentage Error — erro percentual|
| **Coeficientes de correlação**   | Pearson, Spearman — correlação entre sinais     |
| **Tolerance levels**             | Bandas de tolerância (e.g., ±5% do valor nominal)|
| **Simulink Test**                | Framework do MATLAB para teste de modelos       |

---

## Success Criteria

No contexto do estado da arte, critérios de sucesso para verificação automatizada
incluem:

- **Cobertura de requisitos:** Percentual de requisitos cobertos por simulações
  automatizadas
- **Taxa de detecção de defeitos:** Capacidade de identificar requisitos
  inconsistentes, incompletos ou conflitantes
- **Reprodutibilidade:** Resultados de verificação devem ser reproduzíveis em
  execuções independentes
- **Tempo de execução:** Viabilidade de execução em pipelines de CI/CD
- **Robustez MTL:** Margem quantitativa de conformidade

---

## Contribuições Acadêmicas Recentes

A revisão da literatura identifica as seguintes contribuições relevantes:

| Ano  | Contribuição                                                         |
|------|----------------------------------------------------------------------|
| 2024 | Verificação formal de modelos SysML v2 com semântica melhorada       |
| 2023 | Validação virtual hierárquica para sistemas aeroespaciais complexos  |
| 2022 | Digital twins para verificação contínua de requisitos em operação    |
| 2021 | Runtime verification com MTL para detecção de anomalias em voo       |
| 2020 | Detecção de anomalias em dados de simulação com aprendizado de máquina|

---

## Requisitos Vampiros (*Requirement Vampires*)

### Definição

O termo **"requisito vampiro"** é uma expressão informal utilizada na comunidade
de engenharia de sistemas para designar requisitos **mal definidos, vagos e não
verificáveis** que "sugam" recursos do projeto sem contribuir para a qualidade
do produto. Características de requisitos vampiros:

- Utilizam **termos vagos** sem quantificação: "o sistema deve ser rápido",
  "a resposta deve ser adequada", "o desempenho deve ser suficiente"
- **Não possuem critérios de sucesso** mensuráveis ou objetivos
- São **não verificáveis** por qualquer método (I, A, D ou T)
- Consomem esforço de análise e discussão sem convergir para um critério objetivo
- Propagam ambiguidade para fases posteriores do desenvolvimento

### Prevenção e Detecção

A literatura recomenda as seguintes práticas para prevenção e detecção de vampiros:

1. **Escrever requisitos verificáveis:** Utilizar linguagem quantitativa com valores
   numéricos, unidades, tolerâncias e condições de contorno explícitas.
2. **Definir critérios de sucesso antecipadamente:** Estabelecer critérios de
   aceitação no momento da especificação do requisito, não após a implementação.
3. **Rastrear metadados:** Manter atributos de requisitos (verificação, status,
   método) atualizados para identificar lacunas.
4. **Automatizar a detecção:** Utilizar ferramentas que analisem automaticamente
   o texto de requisitos e identifiquem padrões linguísticos associados a
   ambiguidade e não verificabilidade.

---

## Lacuna Identificada na Literatura

A revisão do estado da arte identifica uma **lacuna significativa** no ecossistema
de ferramentas disponíveis:

> **Não existe uma ferramenta standalone, leve e baseada em Python que imponha a
> definição de critérios de sucesso no momento da entrada do requisito e automatize
> a verificação por simulação com geração de DVM (Design Verification Matrix).**

As ferramentas existentes apresentam as seguintes limitações:

| Ferramenta       | Limitação                                                      |
|------------------|----------------------------------------------------------------|
| **IBM DOORS**    | Pesada, cara, sem integração nativa com simulação              |
| **Jama Connect** | Foco em gestão de requisitos, não em verificação automatizada  |
| **Polarion**     | Complexa, requer infraestrutura significativa                  |
| **Simulink Test**| Específica para ecossistema MATLAB, não standalone             |

---

## Relação com o SimReqValidator

O estado da arte fundamenta o SimReqValidator como uma contribuição original que
preenche a lacuna identificada:

1. **Preenchimento da Lacuna:** O SimReqValidator é uma ferramenta standalone,
   leve, baseada em Python, que integra gestão de requisitos com verificação
   automatizada por simulação — exatamente o que a literatura identifica como
   ausente no ecossistema atual.

2. **MTL no TemporalEvaluator:** Os conceitos de Metric Temporal Logic informam
   o design do módulo **TemporalEvaluator** do SimReqValidator, que avalia
   propriedades temporais de sinais de simulação contra critérios de aceitação
   baseados em tempo. A semântica robusta de MTL pode ser utilizada para calcular
   margens de design.

3. **Detecção Automatizada de Vampiros:** O conceito de "requisitos vampiros" é
   implementado como um **portão de qualidade automatizado** (*automated quality
   gate*) no SimReqValidator. A ferramenta analisa requisitos na entrada e
   identifica padrões linguísticos e estruturais associados a não verificabilidade.
   Esta é uma contribuição **inovadora** em relação às ferramentas existentes.

4. **Geração Automática de DVM:** O SimReqValidator gera automaticamente a
   **Design Verification Matrix** a partir dos resultados de simulação, um recurso
   que ferramentas de gestão de requisitos tradicionais (DOORS, Jama) não oferecem
   nativamente.

5. **Integração com Pipelines CI/CD:** A arquitetura do SimReqValidator é
   compatível com o conceito emergente de **DEMOps**, permitindo integração em
   pipelines de integração contínua para verificação automatizada a cada iteração
   de desenvolvimento.

6. **Validação por Métricas Quantitativas:** As metodologias de validação de
   modelos (RMSE, MAPE, correlação, tolerância) são implementadas como
   **evaluators** no SimReqValidator, fornecendo métricas padronizadas para
   avaliação de conformidade.

7. **Abordagem Shift-Left:** Alinhado com o estado da arte, o SimReqValidator
   implementa a filosofia shift-left ao permitir verificação por simulação nas
   fases iniciais do desenvolvimento, antes da disponibilidade de hardware ou
   protótipos físicos.

---

## Citações / Notas

- A convergência de MBSE, simulação automatizada e CI/CD representa uma tendência
  crescente na engenharia de sistemas moderna, validando a relevância temporal
  da ferramenta SimReqValidator.

- A MTL e sua semântica robusta são ferramentas matemáticas sofisticadas que
  permitem uma avaliação mais nuançada de conformidade, indo além do simples
  pass/fail binário para fornecer informação quantitativa sobre margens de design.

- O conceito de "requisito vampiro", embora informal, captura uma deficiência
  real e prevalente na prática de engenharia de requisitos. A detecção automatizada
  destes requisitos é uma contribuição potencialmente significativa.

- A lacuna identificada na literatura fornece a **justificativa acadêmica** para
  o desenvolvimento do SimReqValidator como contribuição original de pesquisa.

- O SysML v2, ainda em fase de adoção, promete melhorar significativamente a
  capacidade de verificação automatizada. O SimReqValidator deve considerar
  compatibilidade futura com esta evolução.

- A integração de conceitos de digital twins com verificação de requisitos
  (contribuições de 2022) sugere direções futuras para o SimReqValidator,
  incluindo verificação contínua em operação (*in-service verification*).

> **Nota metodológica:** Este fichamento sintetiza múltiplas fontes acadêmicas e
> industriais, representando o estado da arte consolidado até 2024. As referências
> específicas (autores, títulos, venues) devem ser incluídas na versão final da
> dissertação conforme as normas ABNT aplicáveis. A identificação da lacuna é
> resultado da análise comparativa entre as capacidades das ferramentas existentes
> e as necessidades identificadas na revisão da literatura.
