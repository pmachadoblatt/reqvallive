# NASA MSFC-HDBK-3173 — Systems Engineering Handbook

## Dados Bibliográficos

- **Título:** Marshall Space Flight Center Systems Engineering Handbook
- **Identificador:** MSFC-HDBK-3173
- **Organização:** National Aeronautics and Space Administration (NASA), Marshall Space Flight Center (MSFC)
- **Referência complementar:** NASA/SP-2016-6105 (NASA Systems Engineering Handbook)
- **Área:** Engenharia de Sistemas — Verificação e Validação de Requisitos
- **Aplicação:** Programas e projetos espaciais gerenciados pelo MSFC

---

## Conceitos-Chave

### Métodos Fundamentais de Verificação e Validação (IADT)

O handbook define quatro métodos fundamentais de V&V, conhecidos pelo acrônimo **IADT**:

1. **Inspection (Inspeção):** Exame visual ou qualitativo de um item, componente ou
   sistema. Inclui revisão de documentação técnica, desenhos de engenharia e
   especificações. Não requer instrumentação especializada nem coleta de dados
   quantitativos. É aplicável quando a conformidade pode ser determinada por
   observação direta.

2. **Analysis (Análise):** Utilização de modelagem matemática, simulação
   computacional e técnicas analíticas para verificar o atendimento a requisitos.
   Este método é particularmente relevante quando testes físicos são impraticáveis,
   excessivamente custosos ou quando as condições operacionais não podem ser
   reproduzidas em ambiente controlado. A análise pode incluir simulações numéricas,
   modelos de elementos finitos, análises estatísticas e simulações de Monte Carlo.

3. **Demonstration (Demonstração):** Execução funcional do sistema ou subsistema
   para mostrar que ele opera conforme especificado, porém sem coleta detalhada
   de dados instrumentados. Difere do teste pela ausência de medições quantitativas
   rigorosas. É utilizada para verificar funcionalidades de alto nível ou requisitos
   qualitativos.

4. **Test (Teste):** Método preferido pela NASA. Envolve a operação do sistema em
   condições controladas com instrumentação adequada para coleta de dados
   quantitativos. Permite a comparação direta entre resultados medidos e critérios
   de sucesso pré-definidos. Inclui testes ambientais, funcionais, de desempenho,
   de qualificação e de aceitação.

### Métodos Complementares

Além dos quatro métodos primários, o handbook reconhece:

- **Similarity (Similaridade):** Comparação com um sistema previamente verificado e
  validado que possui características de design e desempenho equivalentes. Requer
  documentação formal da base de comparação e justificativa técnica.
- **Validation of Records (Validação de Registros):** Revisão e confirmação de
  registros de verificação existentes como evidência de conformidade.

### Critérios de Sucesso (Success Criteria)

Os critérios de sucesso constituem um dos elementos centrais do framework de V&V do
MSFC e devem considerar:

- **Critérios de desempenho:** Valores numéricos específicos com unidades de medida
  claramente definidas.
- **Limites de teste ambiental:** Faixas de temperatura, pressão, vibração e outros
  parâmetros ambientais sob os quais o sistema deve operar.
- **Tolerâncias e margens:** Expressos na forma `valor nominal ± tolerância`
  (e.g., *500 RPM ± 5 RPM*). As margens de design devem ser explicitamente
  declaradas e rastreáveis aos requisitos de origem.
- **Especificações, restrições e pontos de inspeção:** Parâmetros derivados de
  normas aplicáveis, requisitos regulatórios e boas práticas de engenharia.
- **Hardware effectivity e localização da verificação:** Identificação do hardware
  específico (modelo, número de série, configuração) e do local onde a verificação
  será conduzida (laboratório, campo, simulação).

### Documentação de Critérios de Sucesso

Os critérios de sucesso são formalizados por meio de **DRDs (Data Requirements
Documents)**, especificamente o formulário **STD/SE-VVSC** (Verification and
Validation Success Criteria). Este documento deve ser:

- Submetido como parte do pacote de dados do **PDR (Preliminary Design Review)**
- Baseline estabelecido pelo menos **90 dias antes** do início das atividades de V&V
- Aprovado por todas as partes interessadas relevantes

---

## Métodos de V&V

### VCRM — Verification Cross-Reference Matrix

A **VCRM** é o instrumento central de rastreabilidade de verificação definido pelo
handbook. Suas colunas incluem:

| Coluna                  | Descrição                                                        |
|-------------------------|------------------------------------------------------------------|
| **Requirement ID**      | Identificador único do requisito                                 |
| **Requirement Text**    | Texto completo do requisito (*shall statement*)                  |
| **Source**              | Documento ou especificação de origem                             |
| **Verification Method** | Método de verificação selecionado (I, A, D ou T)                |
| **Verification Level**  | Nível de integração (componente, subsistema, sistema)           |
| **Success Criteria**    | Critérios quantitativos ou qualitativos de aceitação            |
| **Responsibility**      | Organização ou indivíduo responsável pela execução              |
| **Status**              | Estado atual: *Not Started*, *In Work*, *Pass* ou *Fail*        |
| **Evidence/Reference**  | Referência ao relatório, registro ou artefato de evidência      |

A VCRM concentra-se exclusivamente em declarações do tipo **"shall"** (*shall
statements*), que representam requisitos obrigatórios e verificáveis. A matriz é:

- Estabelecida formalmente durante o **PDR**
- Mantida como **documento vivo** ao longo de todo o ciclo de vida do projeto
- Atualizada à medida que atividades de verificação são conduzidas e concluídas
- Referenciada contra os templates padronizados do **NASA/SP-2016-6105**

---

## Success Criteria

O handbook enfatiza que critérios de sucesso devem ser:

1. **Quantificáveis:** Expressos em termos mensuráveis sempre que possível, com
   valores numéricos, unidades e tolerâncias.
2. **Rastreáveis:** Vinculados diretamente ao requisito de origem e à especificação
   técnica aplicável.
3. **Verificáveis:** Passíveis de avaliação objetiva por meio de pelo menos um dos
   métodos IADT.
4. **Completos:** Cobrindo todas as condições operacionais, ambientais e de contorno
   relevantes para o requisito.
5. **Pré-definidos:** Estabelecidos antes da execução da atividade de verificação,
   evitando viés de confirmação.

A ausência de critérios de sucesso bem definidos é tratada como uma **não
conformidade** no processo de engenharia de sistemas do MSFC, o que reforça a
importância de mecanismos automatizados de detecção de deficiências.

---

## Relação com o SimReqValidator

O NASA MSFC-HDBK-3173 fornece fundamentação direta para diversas decisões de
design do SimReqValidator:

1. **Método de Análise por Simulação:** O SimReqValidator implementa o método
   "Analysis" (A) da taxonomia IADT, utilizando simulação computacional como
   mecanismo primário de verificação. A ferramenta reconhece que a simulação é um
   substituto aceito pela NASA quando testes físicos são inviáveis, custosos ou
   prematuros no ciclo de desenvolvimento.

2. **Geração Automática de VCRM/DVM:** A estrutura de dados da VCRM é mapeada
   diretamente para o modelo de dados do SimReqValidator. A ferramenta gera
   automaticamente matrizes de verificação que seguem o formato VCRM, incluindo
   todos os campos obrigatórios: ID do requisito, texto, método de verificação,
   critérios de sucesso, status e evidência.

3. **Imposição de Critérios de Sucesso:** Seguindo a filosofia do handbook de que
   critérios de sucesso devem ser pré-definidos, o SimReqValidator exige a definição
   de critérios de sucesso no momento da entrada do requisito. Requisitos sem
   critérios de sucesso são sinalizados como potenciais **"vampiros"**.

4. **Rastreabilidade Bidirecional:** O conceito de rastreamento entre requisitos,
   métodos de verificação e evidências implementado na VCRM é reproduzido na
   arquitetura de dados do SimReqValidator, garantindo que cada requisito possua
   ligação com seu método de verificação e seus resultados de simulação.

5. **Tolerâncias e Margens:** A convenção `valor ± tolerância` do MSFC é adotada
   pelo SimReqValidator para definição de critérios de aceitação em verificações
   numéricas, permitindo avaliação automatizada de *pass/fail* com margem
   configurável.

---

## Citações / Notas

- O handbook é uma referência essencial para programas espaciais do MSFC e
  representa a aplicação prática dos princípios mais amplos do NASA/SP-2016-6105.
- A ênfase na definição antecipada de critérios de sucesso (90 dias antes da V&V)
  reforça o conceito de **shift-left** implementado pelo SimReqValidator, que
  antecipa a verificação para fases iniciais do desenvolvimento.
- A preferência pelo método de teste (*Test*) como método primário é reconhecida,
  porém o handbook explicitamente aceita a análise por simulação como método válido
  e necessário, especialmente em fases de design preliminar e detalhado.
- A VCRM como documento vivo alinha-se com a abordagem do SimReqValidator de
  atualização contínua do status de verificação à medida que novas simulações são
  executadas.
- A estrutura DRD/STD-SE-VVSC pode servir como base para futuras extensões do
  SimReqValidator que gerem relatórios formais de critérios de sucesso compatíveis
  com o formato NASA.

> **Nota metodológica:** Este fichamento concentra-se nos aspectos do handbook
> diretamente aplicáveis à verificação de requisitos por simulação. Seções
> relativas a gestão programática, controle de configuração e revisões formais
> de design foram consultadas mas não detalhadas, por estarem fora do escopo
> imediato da ferramenta SimReqValidator.
