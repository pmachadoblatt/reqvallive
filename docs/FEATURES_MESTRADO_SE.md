# Features necessárias — ReqValLive como PoC válida para mestrado em Engenharia de Sistemas

**Objetivo deste documento:** listar o que o aplicativo **já precisa ter / ainda deve ganhar** para sustentar uma dissertação de **Engenharia de Sistemas** (não um mestrado de “app full-stack”). O valor acadêmico está no ciclo de **V&V**, **Success Criteria**, **evidência** e **rastreabilidade** — o software é o veículo da prova de conceito.

**Documentos irmãos:**
- `ESCOPO_DISSERTACAO.md` — fronteiras e claim
- `PLANO_GATE_SUCCESS_CRITERIA.md` — desenho do gate
- `reference/_markdown/` — Methods (SIS-08) e Conceito de Funcionamento

**Legenda de prioridade**

| Tag | Significado |
|-----|-------------|
| **P0** | Obrigatório para fechar o mestrado (sem isto o claim SE não fecha) |
| **P1** | Fortemente recomendado (eleva rigor SE / banca) |
| **P2** | Desejável / diferencial (SARITA, usabilidade) — não bloqueia defesa |
| **BASE** | Já existe em grande parte na PoC atual (manter / consolidar) |

---

## 1. Princípio: o que “válido para mestrado em SE” significa aqui

Para Engenharia de Sistemas, o app é válido se permitir **demonstrar com evidência** que:

1. Requisitos têm **Success Criteria** explicitados e **aprováveis antes** da atividade de V&V.
2. O método de V&V (**Test**, no MVP) é **coerente** com o tipo de evidência coletada.
3. A medição produz **veredicto auditável** (PASS/FAIL) ligado ao critério — não só um dashboard.
4. Há **rastreabilidade** mínima: requisito ↔ critério ↔ telemetria ↔ laudo ↔ (esqueleto) SysML.
5. O ciclo foi exercitado em **missão real de laboratório** (drones CONCEPTIO + MQTT padronizado).

Não é requisito de mestrado SE: multi-tenant cloud, UX polida de produto, certificação, ou simulação funcional no CATIA Magic.

---

## 2. Mapa do ciclo SE que o app deve cobrir

```text
[Requisito] → [Success Criteria] → [Gate ACCEPT/REJECT]
       ↓                                    ↓ ACCEPT
[Método V&V = Test]              [Pré-condições / ambiente]
       ↓                                    ↓
[Procedimento de medição live] ←—— [MQTT padronizado / drones reais]
       ↓
[Evidência temporal] → [Veredicto] → [Laudo] → [Esqueleto SysML]
       ↓
[Rastreabilidade & configuração leve do critério aprovado]
```

Cada bloco abaixo traduz isso em **features**.

---

## 3. Features por bloco de Engenharia de Sistemas

### 3.1 Requisitos verificáveis (entrada)

| ID | Feature | Prioridade | Por quê (SE) | Status / nota |
|----|---------|------------|--------------|---------------|
| F-REQ-01 | Ingestão de requisitos (Markdown e/ou JSON schema Vampire) | **BASE** | Artefato de requisitos formalizável | Já existe |
| F-REQ-02 | Campos SE mínimos por requisito: `req_id`, texto, `level`, `rationale`, `conops_ref`, `vv_method`, `priority` | **P0** | Rastreio e nível (missão/sistema/…) | Parcial — reforçar obrigatoriedade no gate |
| F-REQ-03 | Interpretação assistida por LLM **opcional**, sempre sujeita a validação | **BASE** | LLM não substitui engenheiro de sistemas | Já existe |
| F-REQ-04 | Edição / correção do requisito e do SC **antes** da medição (após REJECT) | **P1** | Ciclo “submit → review → approve” do MSFC | Gap UX — reavaliar via API já previsto |
| F-REQ-05 | Template / modelo pedagógico de SC (8 dimensões MSFC) | **BASE/P1** | Alinha usuário ao Methods | Modelo já iniciado (`success_criteria_model`) |

### 3.2 Success Criteria (núcleo do mestrado)

| ID | Feature | Prioridade | Por quê (SE) | Status / nota |
|----|---------|------------|--------------|---------------|
| F-SC-01 | Representação estruturada SC: tipo, métrica, operador/faixa, unidade, scope, tolerance | **P0** | SC detalhado e específico (MSFC) | **BASE** |
| F-SC-02 | **Gate ACCEPT/REJECT** com motivos por dimensão MSFC + Method×Success | **P0** | Aprovação do critério **antes** da atividade de V&V | **BASE** (motor); UI completa ainda P1 |
| F-SC-03 | Coerência **vv_method × Success Criteria** (só Test live no MVP) | **P0** | Nota central Methods / assignment | **BASE** |
| F-SC-04 | Checagem de texto **não mensurável** (“adequado”, “bom desempenho”) | **P0** | “Requirements verifiable as written” | **BASE** |
| F-SC-05 | Warnings vs errors (tolerância, CONOPS, environment) sem bloquear à toa | **P1** | Madureza sem burocracia artificial | Parcial |
| F-SC-06 | Campos / metadados de **Environment, Restrictions, Checkpoints** (mesmo que Markdown estruturado) | **P1** | Fecha as 8 considerações MSFC na PoC | Parcial — expandir no modelo + gate |
| F-SC-07 | Congelar **versão do SC aprovado** ligada à sessão/laudo | **P0** | Configuration control * leve* (o que valeu na run) | Gap — implementar |
| F-SC-08 | Sugestões de reescrita quando REJECT | **P1** | Fecha o loop de verifiability | Parcial no motor |

### 3.3 Método V&V e procedimento

| ID | Feature | Prioridade | Por quê (SE) | Status / nota |
|----|---------|------------|--------------|---------------|
| F-VV-01 | Declaração explícita do método (MVP: `test`) na sessão e no laudo | **P0** | DVM / relação method–evidence | Quase BASE |
| F-VV-02 | Bloquear connect/start se gate ≠ ACCEPT | **P0** | Não executar V&V com SC imaturo | **BASE** |
| F-VV-03 | Separar **conectar telemetria** de **iniciar medição** (janela de evidência) | **BASE** | Procedimento ≠ infraestrutura | Já existe |
| F-VV-04 | Pré-condições de missão (ex.: ≥2 drones com GPS para separação) visíveis antes do start | **P1** | Restrictions / environment | Parcial |
| F-VV-05 | Encerrar medição com freeze dos resultados | **BASE** | Fim controlado da atividade de V&V | Já existe |

### 3.4 Evidência live (telemetria real)

| ID | Feature | Prioridade | Por quê (SE) | Status / nota |
|----|---------|------------|--------------|---------------|
| F-EV-01 | Ingestão MQTT conforme **protocolo padronizado do lab** | **P0** | Evidência real, contrato conhecido | **BASE** (Conceptio) |
| F-EV-02 | Multi-entidade (`droneName`) e métricas por entidade + agregadas | **P0** | Missões multiagente | **BASE** |
| F-EV-03 | Avaliação `threshold`/`range`/`statistical(range|max|min)` com regra temporal honesta (`all_timesteps` → **FAIL latch**) | **P0** | Veredicto ≠ último valor; variação = peak-to-peak na janela | **BASE** |
| F-EV-04 | Registrar **atual, mínimo/máximo, 1ª violação, #falhas/amostras** | **P0** | Momentos críticos / evidência objetiva | **BASE** |
| F-EV-05 | Timeline / lista de eventos críticos no laudo (instantes de violação) | **P1** | Narrativa SE da missão | Parcial — aprofundar |
| F-EV-06 | Contagem e qualidade da amostra (perda de link, gaps) | **P1** | Validade da evidência | Gap leve |
| F-EV-07 | Apenas métricas pedidas pelos SC (não “inventar” bateria) | **BASE** | Fidelidade ao requisito | Já existe |

### 3.5 Veredicto, laudo e comunicação de resultados

| ID | Feature | Prioridade | Por quê (SE) | Status / nota |
|----|---------|------------|--------------|---------------|
| F-RP-01 | Laudo PASS/FAIL por requisito com esperado vs observado e *porquê* | **P0** | Produto clássico de V&V | **BASE** |
| F-RP-02 | Secção “O que falhou” + momentos críticos | **P0** | Utilidade para o engenheiro / demo | **BASE**/P1 |
| F-RP-03 | Incluir no laudo: SC aprovado (snapshot), método, protocolo/topic, janela temporal | **P0** | Rastreabilidade do procedimento | Gap — fechar |
| F-RP-04 | Export pack (HTML + MD + CSV amostras + SysML) | **P1** | Entrega ao projeto CET-ADS | Gap |
| F-RP-05 | Integridade leve do laudo (hash do snapshot SC + sumário) | **P2** | Credibilidade acadêmica | Opcional |

### 3.6 Ligação MBSE (esqueleto SysML v2)

| ID | Feature | Prioridade | Por quê (SE) | Status / nota |
|----|---------|------------|--------------|---------------|
| F-MB-01 | Geração de esqueleto SysML v2 (requirement, satisfy, verify, atributos de métrica) | **P0** | Ponte requisito → modelo | **BASE** |
| F-MB-02 | Claim UI/docs: **não é simulação Magic** — apenas partida | **P0** | Honesty SE / banca | Docs — reforçar na UI |
| F-MB-03 | Diagrama visual / Mermaid de apoio à comunicação | **P2** | Comunicação, não prova V&V | **BASE** |
| F-MB-04 | Export `model.md` com notas de SC / MQTT | **P1** | Documentação paralela ao `.sysml` | **BASE** |

### 3.7 Governança leve de sessão (escala lab / SARITA)

| ID | Feature | Prioridade | Por quê (SE) | Status / nota |
|----|---------|------------|--------------|---------------|
| F-GOV-01 | Sessão identificável (id, projeto/missão, timestamps start/end) | **P0** | Unidade de análise empírica | Parcial |
| F-GOV-02 | Campo `project_id` / nome do lab CET-ADS na sessão e no laudo | **P1** | Preparação SARITA | Gap |
| F-GOV-03 | Reavaliar gate após edição (`POST .../criteria/evaluate`) | **BASE** | Ciclo de aprovação | Já existe API |
| F-GOV-04 | Painel “organizador” multi-projeto (visão PASS/FAIL agregada) | **P2** | Útil no SARITA; não fecha o mestrado | Backlog |
| F-GOV-05 | UI passo explícito “Critério de validação” (errors/warnings/sugestões) | **P1** | Torna o método SE visível ao usuário | Backlog changelog |

---

## 4. O que já basta vs. o que falta para “nível mestrado SE”

### Já sustenta a espinha dorsal (manter)

- Gate de Success Criteria + bloqueio de medição  
- MQTT multi-drone + latch temporal de FAIL  
- Laudo PASS/FAIL com esperado vs observado  
- Esqueleto SysML + model.md  
- Alinhamento Methods / MSFC no desenho do gate  

### Lacunas P0 a fechar antes de considerar a PoC “fechada” para a dissertação

1. **Snapshot imutável do SC aprovado** associado à sessão e reproduzido no laudo  
2. **Laudo completo de procedimento:** método, topic/protocolo, janela, SC congelado, evidência crítica  
3. **Metadados de missão** mínimos (nome/projeto, start/end, nº entidades) estáveis no relatório  
4. **Claim do SysML** explícito na UI do export (“esqueleto, não simulação”)  

### Lacunas P1 que a banca de SE tende a valorizar

1. Painel UI do gate (não só JSON/API)  
2. Environment / restrictions / checkpoints mais explícitos no modelo de SC  
3. Timeline rica de violações  
4. Export pack único para o projeto  
5. `project_id` para ensaio multi-lab  

### Explicitamente *não* necessários para validar o mestrado

- Produto SaaS multi-empresa  
- Suporte a todos os métodos V&V como evidência live  
- Runtime Magic / parâmetros `:=` atualizados pela telemetria  
- Escala WARA-PS  

---

## 5. Critérios de aceitação da *ferramenta* (definição de pronto SE)

A PoC é considerada **adequada ao nível de mestrado em Engenharia de Sistemas** quando:

| # | Critério | Evidência |
|---|----------|-----------|
| A | Existe um **método observável** de aprovação de SC antes da run | Gate ACCEPT/REJECT + bloqueio start |
| B | SC rejeitado explica **dimensão SE** (não só “erro de parser”) | Códigos MSFC / Method×Success |
| C | Veredicto live é **fiel ao critério temporal** | Testes de latch + corrida real |
| D | Laudo permite a um SE responder: *o que foi exigido, o que foi medido, passou/falhou, quando* | Relatório com snapshot SC + momentos críticos |
| E | Há ponte MBSE **honesta** | `.sysml` esqueleto + disclaimer |
| F | Ciclo exercitado no **CONCEPTIO** com drones reais / MQTT padronizado | Cap. experimentos da dissertação |
| G | Limites da PoC estão documentados | Escopo + este documento |

---

## 6. Ordem sugerida de implementação (após o que já existe)

1. Snapshot SC aprovado + secção no laudo (P0)  
2. Metadados de missão/procedimento no relatório (P0)  
3. Disclaimer SysML na UI (P0, rápido)  
4. UI do passo “Critério de validação” (P1)  
5. Timeline de violações + export pack (P1)  
6. `project_id` / preparação SARITA (P1–P2)  

---

## 7. Relação com a contribuição da dissertação

| Contribuição SE (dissertação) | Features que a materializam |
|------------------------------|-----------------------------|
| Método de SC executáveis / aprováveis | F-SC-01..08, F-VV-02 |
| Evidência live auditável | F-EV-01..05, F-RP-01..03 |
| Ponte requisito → esqueleto MBSE | F-MB-01..02 |
| Demonstração em arena acadêmica | F-EV-01, F-GOV-01..02, experimentos Conceptio |

O software **não é a contribuição isolada**; ele deve tornar o método **operacional e mensurável**. Features fora dessa tabela são secundárias.

---

## 8. Resumo executivo

Para um mestrado em **Engenharia de Sistemas**, o ReqValLive está no caminho certo se continuar priorizando: **Success Criteria → gate → evidência temporal → laudo rastreável → esqueleto SysML**, com voos reais no CONCEPTIO.  

O que falta para “nível dissertação” não é um produto genérico: é **fechar a rastreabilidade do critério aprovado no laudo**, tornar o **procedimento de V&V explícito**, e **expor o gate** como passo de engenharia — não só como validação interna de API.
)
