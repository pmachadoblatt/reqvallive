# ECSS-E-ST-10-02C — Space Engineering — Verification

## Dados Bibliográficos

- **Título:** ECSS-E-ST-10-02C — Space Engineering — Verification
- **Edição:** Revisão C
- **Organização:** European Cooperation for Space Standardization (ECSS)
- **Área:** Engenharia Espacial — Verificação de Sistemas e Subsistemas
- **Handbook complementar:** ECSS-E-HB-10-02A (Verification Guidelines Handbook)
- **Normas relacionadas:** ECSS-E-ST-10C (System Engineering), ECSS-M-ST-10C
  (Project Planning and Implementation)

---

## Conceitos-Chave

### Métodos de Verificação

O ECSS define quatro métodos de verificação, com nomenclatura ligeiramente distinta
da tradição americana (NASA/IEEE), mas com conceitos equivalentes:

1. **Test (Teste):** Verificação por meio de operação controlada do item sob
   condições definidas, com instrumentação e coleta de dados quantitativos.
   Considerado o método de maior confiança para demonstrar conformidade.

2. **Analysis (Análise):** Verificação por meio de processamento teórico ou
   empírico de dados, utilizando técnicas matemáticas, modelagem, simulação ou
   analogia com sistemas previamente qualificados. Inclui simulação computacional,
   análise de elementos finitos, análises térmicas, dinâmicas e de confiabilidade.

3. **Review of Design (Revisão de Projeto):** Avaliação qualitativa da adequação
   do design em relação aos requisitos, por meio de exame de documentação técnica,
   desenhos, especificações e dados de design. Equivalente funcional da "Inspeção"
   na taxonomia IADT, porém com ênfase na avaliação do design propriamente dito.

4. **Inspection (Inspeção):** Exame visual ou dimensional do item fabricado para
   verificar conformidade com especificações de fabricação, materiais, acabamento
   e montagem. No contexto ECSS, a inspeção tem foco mais específico no produto
   físico, diferente da "Review of Design" que foca na documentação.

### VCD — Verification Control Document

O **VCD (Verification Control Document)** é o artefato central de rastreabilidade
de verificação definido pelo ECSS. É o equivalente europeu da VCRM (NASA), porém
concebido como um **registro dinâmico e rastreável** com estrutura mais elaborada.

O VCD contém os seguintes elementos:

| Campo                         | Descrição                                                    |
|-------------------------------|--------------------------------------------------------------|
| **Requirement ID**            | Identificador único do requisito                             |
| **Requirement Text**          | Texto completo do requisito                                  |
| **Traceability (parent)**     | Rastreabilidade ao requisito de nível superior               |
| **Traceability (child)**      | Rastreabilidade a requisitos de nível inferior               |
| **Verification Method**       | Método selecionado (T, A, RoD ou I)                          |
| **Verification Level/Stage**  | Nível de integração: equipamento, subsistema ou sistema      |
| **Planning Links**            | Referência ao plano de verificação e cronograma              |
| **Compliance Status**         | Estado de conformidade com julgamento de close-out            |
| **Evidence**                  | Referência ao relatório ou artefato de evidência             |
| **Close-out Judgment**        | Decisão formal de encerramento da atividade de verificação   |

A principal distinção do VCD em relação à VCRM é a sua natureza de **documento
dinâmico**: ele é continuamente atualizado ao longo de todo o ciclo de vida do
projeto, desde a fase de definição até o encerramento da verificação. O VCD
também incorpora explicitamente a rastreabilidade hierárquica (parent/child),
um aspecto menos enfatizado na VCRM.

### Estratégia de Verificação e Plano de Verificação

O ECSS distingue entre:

- **Estratégia de Verificação (*Verification Strategy*):** Abordagem de alto nível
  que define os princípios, métodos e filosofia de verificação para o projeto.
  Documentada no **Verification Plan**.

- **Plano de Verificação (*Verification Plan*):** Documento detalhado que especifica
  as atividades de verificação, cronograma, responsabilidades, recursos e critérios
  de aceitação para cada requisito.

### Data Requirements Documents (DRDs)

O ECSS define DRDs específicos para cada tipo de atividade de verificação:

- **Verification Report:** Relatório consolidado de verificação
- **Test Report:** Relatório de teste com dados, análise e conclusões
- **Analysis Report:** Relatório de análise com modelos, dados e resultados
- **Inspection Report:** Relatório de inspeção com observações e conclusões
- **Review Report:** Relatório de revisão de design com avaliações e recomendações

### Abordagem Hierárquica Bottom-Up

O ECSS adota uma abordagem **hierárquica de verificação bottom-up**, que constitui
um dos seus aspectos mais distintivos:

```
┌─────────────────────────────────────┐
│         SISTEMA (System)            │  ← Verificação final integrada
├─────────────────────────────────────┤
│      SUBSISTEMA (Subsystem)         │  ← Verificação de integração
├─────────────────────────────────────┤
│     EQUIPAMENTO (Equipment)         │  ← Verificação de componente
└─────────────────────────────────────┘
```

Nesta abordagem:

1. **Equipamento:** Componentes individuais são verificados primeiro, isoladamente,
   contra seus requisitos de nível de equipamento.
2. **Subsistema:** Conjuntos de equipamentos integrados são verificados contra
   requisitos de nível de subsistema.
3. **Sistema:** O sistema completo é verificado contra requisitos de nível de
   sistema, incluindo requisitos de desempenho de missão.

A verificação em cada nível pode utilizar diferentes métodos: um requisito pode ser
verificado por análise no nível de equipamento e confirmado por teste no nível de
sistema, por exemplo.

---

## Métodos de V&V

A abordagem ECSS para V&V é distinguida pela sua ênfase em:

- **Planejamento antecipado:** A estratégia de verificação é definida nas fases
  iniciais do projeto e refinada progressivamente.
- **Rastreabilidade completa:** Cada atividade de verificação é rastreável ao
  requisito de origem, ao plano de verificação e à evidência de conformidade.
- **Close-out formal:** Cada atividade de verificação requer um julgamento formal
  de encerramento (*close-out judgment*) que confirma a conformidade.
- **Verificação incremental:** A verificação é conduzida incrementalmente ao longo
  do ciclo de vida, não como evento pontual.

---

## Success Criteria

O ECSS trata critérios de sucesso como parte integral do VCD e do plano de
verificação:

- Critérios de aceitação devem ser definidos antes da execução de qualquer atividade
  de verificação
- O **close-out judgment** requer que os resultados sejam formalmente comparados
  com os critérios de aceitação
- Anomalias ou desvios dos critérios devem ser documentados, classificados e
  tratados por meio de processo de não conformidade (*non-conformance process*)
- O status de conformidade no VCD reflete o resultado desta comparação

---

## Relação com o SimReqValidator

O ECSS-E-ST-10-02C é particularmente relevante para o SimReqValidator devido à
sofisticação de sua estrutura de dados e à sua abordagem hierárquica:

1. **Mapeamento Direto do VCD para o Modelo de Dados:** A estrutura do VCD mapeia
   quase diretamente para o modelo de dados do SimReqValidator. Os campos do VCD
   (Requirement ID, Text, Traceability, Verification Method, Level/Stage,
   Compliance, Evidence) correspondem a atributos do modelo de requisitos da
   ferramenta. Esta correspondência valida a completude do modelo de dados proposto.

2. **Rastreabilidade Hierárquica Parent/Child:** A rastreabilidade explícita entre
   requisitos de diferentes níveis (parent/child) implementada no VCD é adotada
   pelo SimReqValidator, permitindo a navegação hierárquica entre requisitos de
   sistema, subsistema e componente.

3. **Abordagem Hierárquica Bottom-Up:** O conceito de verificação em múltiplos
   níveis de integração (equipamento → subsistema → sistema) é aplicável ao
   SimReqValidator. A ferramenta pode executar simulações em diferentes níveis de
   fidelidade, desde modelos simplificados de componentes até simulações integradas
   de sistema.

4. **Close-out como Status de Verificação:** O conceito de *close-out judgment* do
   ECSS informa o design do status de verificação no SimReqValidator: cada
   requisito verificado recebe um julgamento formal (Pass/Fail) baseado na
   comparação automatizada entre resultados de simulação e critérios de sucesso.

5. **DRDs como Templates de Relatório:** Os DRDs específicos por tipo de atividade
   (Analysis Report, Test Report) fornecem templates para os relatórios gerados
   automaticamente pelo SimReqValidator, particularmente o Analysis Report.

6. **Documento Dinâmico:** A filosofia do VCD como documento vivo e continuamente
   atualizado é implementada no SimReqValidator, onde o status de verificação é
   atualizado automaticamente a cada execução de simulação.

---

## Citações / Notas

- O ECSS é o framework de engenharia espacial adotado pela Agência Espacial
  Europeia (ESA) e pelas agências espaciais nacionais europeias, sendo amplamente
  reconhecido como referência para projetos espaciais de alta confiabilidade.

- A distinção entre "Review of Design" e "Inspection" no ECSS oferece uma
  granularidade maior que a taxonomia IADT tradicional, refletindo a ênfase
  europeia na revisão formal de design como atividade de verificação distinta.

- O handbook complementar ECSS-E-HB-10-02A fornece diretrizes detalhadas e
  exemplos práticos para a aplicação da norma, sendo uma referência valiosa
  para a implementação do SimReqValidator.

- A abordagem hierárquica bottom-up é particularmente relevante para sistemas
  aeroespaciais complexos como UTM (Unmanned Traffic Management), onde
  verificação em múltiplos níveis de integração é necessária.

- A estrutura do VCD é mais rica que a VCRM da NASA, especialmente na
  rastreabilidade hierárquica e no processo de close-out formal. O SimReqValidator
  incorpora elementos de ambas as abordagens.

> **Nota metodológica:** Este fichamento concentra-se na norma ECSS-E-ST-10-02C
> propriamente dita. O handbook complementar ECSS-E-HB-10-02A foi consultado
> para contextualização, mas seu conteúdo detalhado não está incluído neste
> documento. A análise comparativa entre a abordagem ECSS e a abordagem NASA/IEEE
> é um aspecto relevante para trabalhos futuros.
