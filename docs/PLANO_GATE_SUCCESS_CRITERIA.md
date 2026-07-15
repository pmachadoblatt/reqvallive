# Plano: Gate de Aceite/Recusa do Critério de Validação (antes da medição)

**Objetivo:** definir o que deve ser implementado no ReqValLive para que, **antes de iniciar a medição MQTT**, cada *Success Criterion* (critério de sucesso/validação) seja **aceito ou recusado**, com motivo explícito da recusa.

**Escopo deste documento:** apenas o plano. **Não altera código.**

**Referências estudadas (nesta pasta):**

| Documento | Contribuição principal para este plano |
|-----------|----------------------------------------|
| `[SIS-08][2025] 05 - Methods.md` (Cerqueira) | Métodos de V&V, coerência Method × Success Criteria, checklist MSFC para definir/aprovar sucesso |
| `CONCEITO DE FUNCIONAMENTO.md` (Cerqueira) | Métricas de efetividade (*Success Criterias*) como ponte arquitetura ↔ simulação live/virtual; coleta e avaliação ok/nok |

---

## 1. O que as referências exigem (síntese)

### 1.1 Success Criteria não são “texto livre”

Segundo o material de Methods (MSFC-HDBK-3173 / NDIA):

- Success Criteria são **critérios detalhados e específicos** que determinam a conclusão bem-sucedida da atividade de V&V.
- Devem estar **prontos e aprovados antes** da execução da verificação/validação (no handbook: idealmente no PDR; no mínimo com margem para redigir procedimentos).
- No ReqValLive, o análogo operacional é: **não iniciar medição** enquanto o critério não estiver **aprovado** pelo gate.

### 1.2 O que considerar ao definir um critério de sucesso

O material lista 8 dimensões a cobrir ao desenvolver Success Criteria:

1. **Performance criteria** — o que medir e o limiar (métrica + operador + valor / faixa)
2. **Environment Test Limits** — em que condições ambientais/operacionais vale a medição
3. **Tolerances** — folga aceitável na observação
4. **Margins** — margens de segurança além do limiar nominal (quando aplicável)
5. **Specifications** — rastreio a especificação / CONOPS / requisito-fonte
6. **Restrictions** — restrições (escopo, entidades, duração mínima, pré-condições)
7. **Checkpoints** — pontos de verificação no tempo ou no cenário
8. **Effectiveness and localization** — eficácia esperada e localização (nível missão/sistema/subsystem; por drone vs. global)

### 1.3 Coerência Method × Success Criteria

O assignment do orientador exige nota em **“Coherent Method x Success”**:

| Método V&V | Tipo de evidência esperada no Success Criteria |
|------------|--------------------------------------------------|
| **Test** | Dados numéricos sob condições controladas (thresholds, ranges, amostras) |
| **Demonstration** | Observação pass/fail / yes-no, sem exigência de data gathering denso |
| **Inspection** | Atributos físicos ou registros visuais (não telemetria contínua) |
| **Analysis** | Modelos, cálculo, similaridade — não exigem MQTT live |
| **Review of Design / Similarity / Records / Process Control** | Evidência documental ou de processo — fora do motor live |

**Regra para ReqValLive:** a medição MQTT live só faz sentido quando o método é **Test** (ou, em casos claros, **Demonstration** com critério observável). Outros métodos → critério **recusado para medição live** (não significa “requisito inválido”; significa “não executável neste gate”).

### 1.4 Papel no conceito de funcionamento

No “Conceito de Funcionamento”, *Success Criteria* ligam:

```text
Definir métricas de sucesso  →  Coletar métricas (Live / Virtual)  →  Avaliação ok/nok
```

O ReqValLive cobre a ramo **Live Simulation**. O gate garante que só se entra em “Coletar métricas” quando a definição de sucesso está **madura o suficiente** para ser avaliada de forma inequívoca (ok/nok).

### 1.5 Requisitos devem ser verificáveis como escritos

Methods: *“SE should ensure all requirements are verifiable as written.”*  
Se o texto do requisito não permitir um critério mensurável, o gate deve **recusar** e sugerir reescrita (como no assignment: *Suggestions for rewriting requirements, to be verifiable*).

---

## 2. Situação atual no ReqValLive (gap)

Fluxo atual (simplificado):

```text
Markdown → LLM → requisitos JSON → SysML/diagrama → MQTT connect → Iniciar medição
```

Já existe:

- Schema Vampire (`simreqvalidator`) com `vv_method` + `success_criteria` (`threshold` / `range`, etc.)
- Checagem parcial `is_mvp_supported()` (tipo threshold/range + métrica “live”)
- Bloqueio duro em `/sessions/{id}/start` se critério não suportado

**O que falta face às referências:**

| Lacuna | Por quê importa |
|--------|-----------------|
| Não há etapa explícita de **aprovação** do Success Criteria | Methods exige submit/approval antes da atividade |
| Recusa pouco explicativa (“não suportado”) | Orientador exige entender *por que* o critério não serve |
| Não valida **coerência `vv_method` × critério** | Nota 1 do assignment |
| Não cobre as 8 dimensões (ambiente, margens, checkpoints, localização…) | MSFC checklist |
| Não há veredicto estruturado **ACCEPT / REJECT** por requisito | Gate de entrada à medição |
| UI passa direto da interpretação à conexão MQTT | Usuário não revisa critério maduro |

---

## 3. Posição do gate no fluxo (o que deve acontecer)

Inserir um passo **obrigatório** entre interpretação/modelo e medição:

```text
1. Markdown / carga de requisitos
2. Interpretação (LLM ou JSON)
3. Geração SysML / diagrama (pode permanecer)
4. ★ GATE: avaliação do Success Criteria (este plano)
      ├─ ACCEPT  → habilita “Conectar / Iniciar medição”
      └─ REJECT  → bloqueia medição + mostra motivos + (opcional) sugerir reescrita
5. MQTT connect
6. Iniciar medição / Encerrar / Relatório
```

**Regra de ouro:** `/start` (e o botão equivalente na UI) só pode funcionar se **todos** os requisitos da sessão tiverem critério **ACCEPT**, ou se o utilizador tiver aceite formalmente uma sessão “parcial” (fora do MVP; ver secção 7).

---

## 4. O que implementar: motor de avaliação do critério

### 4.1 Novo conceito: `CriteriaGateResult`

Por requisito, o sistema deve produzir algo deste género (conceitual):

```text
req_id
status: ACCEPT | REJECT
reasons[]: { code, severity, message, dimension }
suggestions[]: texto de reescrita / preenchimento
method_coherence: ok | fail
live_executable: true | false
```

- `ACCEPT` → critério aprovado **para medição live nesta ferramenta**
- `REJECT` → recusado; medição bloqueada; motivos obrigatórios

### 4.2 Dimensões de verificação (checklist do gate)

Cada dimensão abaixo deve gerar zero ou mais `reasons` com código estável (para UI e testes).

#### A. Completude do critério (Performance criteria)

| Código | Recusar quando… |
|--------|-----------------|
| `SC_MISSING` | Ausência de `success_criteria` |
| `SC_TYPE_UNSUPPORTED` | Tipo fora do conjunto live (`threshold`/`range` no MVP) |
| `SC_METRIC_MISSING` | Sem `metric` |
| `SC_OPERATOR_MISSING` | Threshold sem operador válido |
| `SC_VALUE_MISSING` | Threshold sem `value` numérico |
| `SC_RANGE_INVALID` | Range incompleto ou `min > max` |
| `SC_UNIT_MISSING` | Unidade ausente quando a métrica a exige (%, m, …) |
| `SC_TEXT_NOT_MEASURABLE` | Texto do requisito ambíguo / não mensurável (“deve ser adequado”, “bom desempenho”) |

#### B. Coerência Method × Success (Methods / assignment)

| Código | Recusar quando… |
|--------|-----------------|
| `VV_METHOD_MISSING` | Sem `vv_method` |
| `VV_METHOD_NOT_LIVE` | Método é inspection / analysis / review_of_design / similarity / … (não gera evidência por telemetria) |
| `VV_METHOD_MISMATCH` | Ex.: `vv_method=test` mas critério é qualitativo; ou `demonstration` com amostragem estatística densa sem justificação |
| `VV_TEST_WITHOUT_NUMERIC` | Método Test sem limiar numérico claro |

#### C. Tolerances & Margins

| Código | Aceitar com aviso / recusar (política) |
|--------|----------------------------------------|
| `SC_TOLERANCE_MISSING` | Threshold crítico de segurança sem `tolerance` definida (pode ser **warn** no MVP; **reject** se prioridade high + tag safety) |
| `SC_MARGIN_UNDEFINED` | Requisitos de safety sem margem explícita (aviso; reject opcional) |

#### D. Environment / Restrictions / Checkpoints

| Código | Recusar ou avisar quando… |
|--------|---------------------------|
| `SC_SCOPE_MISSING` | Sem `scope` (all_entities / all_timesteps / …) |
| `SC_ENV_UNDEFINED` | Sem indicação de condições de teste (altitude máx., número mín. de drones, indoor/outdoor…) — **warn** MVP |
| `SC_CHECKPOINT_UNDEFINED` | Critério temporal (“durante toda a missão”) sem regra operacional (ex.: duração mínima de amostragem) — **warn** ou reject se texto exige “toda a operação” |
| `SC_RESTRICTION_CONFLICT` | Escopo incompatível com métrica (ex.: métrica global `min_separation_m` com scope `per_entity` incoerente) |

#### E. Effectiveness and localization (nível + alvo)

| Código | Recusar quando… |
|--------|-----------------|
| `SC_LEVEL_MISSING` | Sem `level` (mission/system/subsystem/component) |
| `SC_LOCALIZATION_UNCLEAR` | Não dá para saber se avalia por drone, frota, ou par de drones |
| `SC_METRIC_NOT_IN_TELEMETRY` | Métrica inexistente / não mapeável no payload MQTT do lab |
| `SC_AGGREGATION_UNSUPPORTED` | Precisa agregação que o motor ainda não faz (ex.: percentil 95 temporal) |

#### F. Especificação / rastreabilidade

| Código | Aviso ou recusa |
|--------|-----------------|
| `SC_CONOPS_MISSING` | Sem `conops_ref` / ligação a CONOPS — **warn** no MVP |
| `SC_RATIONALE_MISSING` | Sem `rationale` — **warn** |

#### G. Executabilidade live (ponte com o motor atual)

| Código | Recusar quando… |
|--------|-----------------|
| `LIVE_METRIC_UNSUPPORTED` | Métrica não está no registry live |
| `LIVE_NEEDS_MULTI_DRONE` | Ex.: `min_separation_m` mas configuração implícita não garante ≥2 entidades (avisar pré-condição) |
| `LIVE_BOOLEAN_TEMPORAL` | Critério booleano/temporal ainda fora do MVP (alinhado ao CHANGELOG backlog) |

### 4.3 Política ACCEPT vs REJECT (MVP recomendado)

**REJECT (bloqueia medição)** se qualquer razão com severidade `error` existir.

Tratar como `error` no MVP:

- completude numérica (A)
- incoerência Method × Success (B) que impede Test live
- métrica não executável / agregação não suportada (E/G)
- texto não mensurável (A)

Tratar como `warning` (mostra na UI, **não** bloqueia sozinho):

- CONOPS/rationale ausentes
- environment/checkpoint pouco especificados
- tolerância/margem omitidas (exceto regra safety high, se se optar por endurecer)

**ACCEPT** somente se:

1. zero `error`
2. `vv_method` ∈ {`test`} (MVP; opcionalmente `demonstration` com pass/fail telemetría simples)
3. `live_executable == true`
4. critério coerente com o texto do requisito (checagem heurística + schema)

### 4.4 Mensagens de recusa (contrato de UX)

Cada recusa deve responder a três perguntas na UI/API:

1. **O que falhou?** (código + dimensão MSFC/Methods)
2. **Por quê?** (frase objetiva, em português)
3. **Como corrigir?** (`suggestions[]` — reescrita do requisito ou do critério)

Exemplo:

```text
REJECT · RQ-BAT-001
Código: VV_METHOD_MISMATCH
Dimensão: Method × Success
Motivo: vv_method=inspection, mas o critério exige amostragem contínua de batteryLevel via MQTT.
Sugestão: alterar vv_method para "test" ou remover este requisito da sessão de medição live.
```

---

## 5. O que implementar: integração no produto (sem detalhar código aqui)

### 5.1 Backend (conceito)

1. **Módulo novo** tipo `eval/criteria_gate.py` (ou nome equivalente) que:
   - recebe `RequirementRecord` (+ opcionalmente markdown fonte)
   - devolve `CriteriaGateResult` por requisito e um resumo da sessão
2. **Invocação automática** após:
   - interpretação LLM (`/requirements/from-markdown*`)
   - criação de sessão JSON (`/sessions`)
3. **Persistência no estado da sessão:**
   - `criteria_gate: { status, results[], accepted_at?, ... }`
4. **Endpoint opcional de revalidação:**
   - `POST /sessions/{id}/criteria/evaluate` (após edição manual do critério)
5. **Endurecer `/start`:**
   - recusar start se gate ≠ ACCEPT global
   - devolver 409/422 com lista de motivos (não só “não suportado”)

### 5.2 UI (conceito)

Novo passo visível: **“4. Critério de validação”** (antes de MQTT/medição):

- Tabela por requisito: método, métrica, limiar, status ACCEPT/REJECT
- Painel de motivos (errors + warnings)
- Botões: *Reavaliar*, *Editar critério* (futuro), *Não iniciar medição*
- Botões MQTT / Iniciar medição **desabilitados** até ACCEPT

Diagrama:

```text
┌─────────────┐   ┌──────────────┐   ┌─────────────────────┐   ┌──────┐   ┌──────────┐
│ Requisitos  │ → │ SysML/Model  │ → │ Gate Success Crit.  │ → │ MQTT │ → │ Medição  │
└─────────────┘   └──────────────┘   │ ACCEPT / REJECT     │   └───┬──┘   └────┬─────┘
                                     └─────────────────────┘       │           │
                                              │ REJECT             └─ bloqueado se REJECT
                                              ▼
                                     motivos + sugestões
```

### 5.3 Relatório HTML

Quando houver medição, o relatório deve incluir secção:

- **Critérios aprovados no gate** (versão congelada do critério aceito)
- Motivos históricos se houve reavaliação

Isto alinha-se ao Methods: critérios sob “controle” antes da execução.

### 5.4 LLM

Ajustar o prompt para **já gerar** campos que o gate exige (quando possível):

- `vv_method` coerente com Test live
- `tolerance`, `scope`, `unit`, `conops_ref`, `rationale`
- não inventar critérios; marcar incerteza em vez de inventar limiares

O gate **valida** a saída do LLM; o LLM não substitui o gate.

### 5.5 Testes

Suite dedicada (fixtures ACCEPT/REJECT) cobrindo pelo menos:

- threshold completo + `vv_method=test` + métrica MQTT → ACCEPT  
- `vv_method=inspection` + threshold → REJECT `VV_METHOD_NOT_LIVE` / `MISMATCH`  
- range `min > max` → REJECT  
- métrica desconhecida → REJECT `SC_METRIC_NOT_IN_TELEMETRY` / `LIVE_METRIC_UNSUPPORTED`  
- texto vago → REJECT `SC_TEXT_NOT_MEASURABLE`  
- `start` com REJECT na sessão → HTTP de bloqueio  

Alinhar exemplos em `examples/` ao contrato do gate.

---

## 6. Critérios de aceite deste plano (definição de pronto do *feature*)

O feature estará completo quando:

1. Após carregar/interpretar requisitos, a UI/API mostra **ACCEPT ou REJECT por requisito**, com motivos.
2. É impossível iniciar medição com algum critério em REJECT (salvo modo futuro explícito).
3. Motivos citam dimensões alinhadas a Methods/MSFC (não só “unsupported”).
4. Coerência **Method × Success** é verificada de forma explícita.
5. Utilizador entende **como corrigir** (sugestões).
6. Testes automatizados cobrem os casos da secção 5.5.

---

## 7. Fora de escopo do MVP (backlog consciente)

- Aprovação humana formal / assinatura digital (configuration control real do handbook)
- Edição rica do critério na UI (versionamento formal)
- Critérios booleanos / temporais / estatísticos avançados
- Suporte live a Inspection/Analysis (outro tipo de evidência)
- Sessões com medição parcial (só requisitos ACCEPT) — útil, mas política de produto a decidir

---

## 8. Ordem sugerida de implementação (quando for codificar)

1. Especificar códigos de razão + severidades (contrato estável)
2. Implementar motor `criteria_gate` puro (sem UI)
3. Ligar à sessão + bloquear `/start`
4. Expor no `to_public_dict` / SSE
5. Passo na UI + desabilitar medição
6. Endurecer prompt LLM + testes + exemplos
7. Secção no relatório HTML

---

## 9. Resumo executivo

As referências do orientador tratam Success Criteria como **artefato aprovável antes da atividade de V&V**, com checklist (performance, ambiente, tolerâncias, margens, specs, restrições, checkpoints, localização) e **coerência obrigatória com o método de V&V**.

O ReqValLive hoje avalia o resultado live, mas **não formaliza a aprovação do critério**. O que deve ser implementado é um **gate ACCEPT/REJECT** entre a interpretação dos requisitos e a medição MQTT, com motivos estruturados e bloqueio de medição em caso de REJECT — de forma que a ferramenta opere como uma mini-instanciação do fluxo “definir métricas de sucesso → aprovar → coletar → ok/nok” do Conceito de Funcionamento.
)
