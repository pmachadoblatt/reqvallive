# Escopo da Dissertação — ReqValLive

**Título provisório:**  
Validação live de Success Criteria em missões multiagente: do requisito verificável à evidência telemetrada e ao esqueleto SysML v2 (prova de conceito no laboratório CONCEPTIO / CET-ADS)

**Candidato:** Pedro  
**Orientação / contexto:** CONCEPTIO (ITA) · CET-ADS · linhagem metodológica SIS-08 Methods / Virtual Demonstrator (ADS-VD)  
**Artefato de software:** ReqValLive (prova de conceito)

**Natureza:** dissertação de mestrado com contribuição metodológica + ferramenta demonstrável em escala de laboratório acadêmico.  
**Não é:** adoção industrial, plataforma WARA-PS, nem substituto de ferramentas MBSE comerciais; o SysML exportado **não** pretende ser simulação funcional no CATIA Magic.

---

## 1. Contexto e motivação

O **CET-ADS** (*Centro de Desenvolvimento de Tecnologias Críticas para o Domínio Aéreo Futuro*) articula projetos do Air Domain Study (ADS) no ecossistema CONCEPTIO. O **ADS-VD (Virtual Demonstrator)** tem como resultado esperado, entre outros:

- sistemática de eventos para demonstrações dos projetos;
- ambiente que permita a **medição das métricas desejadas** e a avaliação cruzada de projetos.

Na prática, demos acadêmicos multiagente ainda sofrem de um gap recorrente:

1. requisitos / métricas de sucesso pouco formalizados **antes** da run;
2. telemetria rica **durante** a demo sem laudo auditável **depois**;
3. ausência de um ponto de partida MBSE (esqueleto SysML v2) ligado ao que foi validado — sem exigir do operador montar o modelo do zero.

Paralelamente, a exploração de simulação SysML (e.g. CATIA Magic) mostrou limite para refletir telemetria live — motivando uma prova de conceito **standalone** que preserve a disciplina de Success Criteria, avalie evidência MQTT em voo real, e ainda exporte um **esqueleto** SysML v2 para reuso opcional pelo projeto.

### Âncora empírica principal: laboratório CONCEPTIO

A validação da PoC **não depende** da ocorrência do evento SARITA. O CONCEPTIO dispõe de **drones reais** que publicam telemetria no **MQTT do laboratório**. As experimentações da dissertação usam **missões simuladas de cenário** (roteiros de demonstração acadêmica) executadas com essa frota real — isto é: voo e dados reais, missão com propósito de teste/validação do ciclo SC → evidência → laudo.

### Extensão desejável: SARITA (CET-ADS)

Se / quando o **SARITA** ocorrer (integração acadêmica dos laboratórios CET-ADS), o mesmo ciclo pode ser ensaiado entre projetos. Nesse caso, **os payloads serão uniformizados** conforme o **documento de padronização do protocolo MQTT** já existente no lab — removendo a hipótese de adapters heterogêneos como risco central da dissertação.

---

## 2. Problema de pesquisa

**Como viabilizar, em escala de laboratório acadêmico (CONCEPTIO), um ciclo operacional em que requisitos com Success Criteria sejam aprovados antes da run, a telemetria real de drones via MQTT seja avaliada durante missões de teste, e ao final se obtenha um laudo PASS/FAIL com momentos críticos mais um esqueleto SysML v2 reutilizável — com extensibilidade natural a eventos de integração CET-ADS (SARITA) sob protocolo MQTT padronizado?**

### Perguntas derivadas

1. Que checklist / regras tornam um Success Criterion **aceitável** para medição live antes da execução (gate ACCEPT/REJECT)?
2. Como garantir que o veredicto live respeite o sentido temporal do critério (e.g. `all_timesteps`), e não só o último valor amostrado?
3. O ciclo *Markdown/requisito → SC aprovado → MQTT (protocolo lab) → laudo + esqueleto SysML* é realizável de ponta a ponta com drones reais em missões de teste no CONCEPTIO?

---

## 3. Objetivos

### Objetivo geral

Propor e demonstrar um **método e uma prova de conceito** (ReqValLive) para validação live de Success Criteria em missões multiagente de laboratório, alinhado às práticas de V&V (métodos, coerência Method × Success, aprovação do critério antes da atividade) e ao papel de medição de métricas esperado no ADS-VD / CET-ADS.

### Objetivos específicos

1. Formalizar um **gate de Success Criteria** (ACCEPT/REJECT + motivos) antes da medição, inspirado em SIS-08 Methods / MSFC-HDBK-3173 (performance, tolerâncias, escopo, localização, coerência com método de V&V).
2. Implementar avaliação live de critérios `threshold`/`range` contra telemetria MQTT multi-entidade (**drones reais**, protocolo do lab), com evidência temporal íntegra (latch de FAIL, 1ª violação, extremos, contagem).
3. Gerar artefatos pós-missão: **relatório** (PASS/FAIL, esperado vs observado, momentos críticos) e **esqueleto SysML v2** textual (ponto de partida MBSE — não runtime de simulação Magic).
4. Demonstrar o ciclo de ponta a ponta no **CONCEPTIO** (obrigatório). Ensaio no **SARITA**, se houver, como extensão sob o mesmo protocolo MQTT padronizado.

---

## 4. Hipótese de trabalho

Se Success Criteria forem (i) tornados verificáveis e aprováveis *antes* da run e (ii) avaliados contra telemetria real de drones com regras temporais explícitas e protocolo MQTT conhecido, então é possível produzir, ao final de missões de teste no laboratório, um laudo e um esqueleto SysML que **fechem o ciclo métrica de sucesso → evidência → ok/nok** de forma mais auditável do que demos ad hoc sem critério pré-declarado.

---

## 5. Escopo (o que ENTRA)

| Item | Conteúdo |
|------|----------|
| Domínio | Missões UAS / multiagente em arena acadêmica |
| Base empírica | **CONCEPTIO**: drones reais → MQTT do lab → missões de teste / cenário |
| Telemetria | Protocolo MQTT **padronizado** do laboratório (documento de padronização existente); no SARITA, payloads **uniformizados** sob esse contrato |
| Evento | SARITA = extensão desejável (integração CET-ADS), **não** pré-requisito de conclusão |
| V&V | Método **Test** com SC numéricos (`threshold` / `range`) |
| Gate SC | ACCEPT/REJECT com códigos de razão e sugestões |
| Runtime | App web local (FastAPI) + subscriber MQTT + sessão de medição |
| Relatório | HTML/MD, evidência de violações / momentos críticos |
| SysML | Export textual `.sysml` / model.md como **esqueleto** para o usuário continuar no seu fluxo MBSE |
| Avaliação | Casos controlados + corridas com drones reais no Conceptio (+ SARITA se ocorrer) |

## 6. Fora de escopo (o que NÃO ENTRA)

- Simulação funcional / runtime live no **CATIA Magic** a partir do `.sysml` gerado
- Substituição de CATIA Magic / Cameo / DOORS como plataforma MBSE oficial
- Escala industrial tipo WARA-PS Demonstration Week
- Multi-tenant cloud, SSO, certificação, configuration control formal de grande organização
- Critérios booleanos / estatísticos avançados / temporais ricos (além do MVP; trabalho futuro)
- Suporte nativo a Inspection / Analysis / Review-of-design como evidência live
- Integração profunda ao core WARA-PS
- Desenvolvimento de um *novo* protocolo MQTT (reutiliza-se o padrão do lab)
- Dependência da realização do SARITA para fechar a dissertação

### Claim explícito sobre o SysML exportado

O artefato SysML v2 serve para o usuário **não partir do zero**: requisitos, atributos de métrica, `satisfy`/`verify` esboçados, topic MQTT e estrutura mínima colável no editor textual.  
**Não se espera** que esse modelo execute simulação equivalente à telemetria live dentro do CATIA Magic. A evidência de V&V live da dissertação está no **ReqValLive + MQTT + laudo**, não no motor de simulação Magic.

---

## 7. Contribuições esperadas

1. **Metodológica:** operacionalização de Success Criteria para medição live em demo/missão acadêmica (gate + coerência Method × Success + evidência temporal).
2. **Tecnológica:** PoC ReqValLive que instancia o ciclo *declarar → aprovar → medir (MQTT real) → laudar → exportar esqueleto SysML*.
3. **Empírica:** demonstração do ciclo com **drones reais** em missões de teste no CONCEPTIO; se o SARITA ocorrer, relato de uso multi-projeto sob protocolo MQTT uniforme.

---

## 8. Metodologia de trabalho

1. **Fundamentação:** V&V methods, Success Criteria (SIS-08 / MSFC), conceito VD (métricas de efetividade; live vs virtual).
2. **Análise do gap:** limite da simulação SysML estática para telemetria live; demos sem SC pré-aprovados.
3. **Desenho do método:** contrato do gate; política ACCEPT/REJECT; regras de evidência (`all_timesteps`, latch).
4. **Implementação PoC:** ReqValLive — gate, medição alinhada ao protocolo MQTT do lab, relatório, gerador de esqueleto SysML.
5. **Experimentação (pilares):**
   - testes unitários / regressão (gate, fail latch);
   - **missões de teste no CONCEPTIO** com drones reais (ex.: bateria, separação, outros SC `threshold`/`range` compatíveis com o payload padronizado);
   - **SARITA** (se ocorrer): projetos sobem requisitos antes; medem com payload uniforme; recebem laudo + esqueleto SysML depois.
6. **Avaliação:** qualidade do gate, fidelidade do laudo à telemetria real, utilidade do esqueleto SysML (ponto de partida, não simulação).
7. **Discussão:** ameaças à validade, escala lab, trabalhos futuros (painel organizador SARITA, mais tipos de SC).

---

## 9. Casos de uso

### 9.1 Caso âncora (obrigatório) — CONCEPTIO

```text
Missão de teste (cenário acadêmico)
  Drones reais  →  MQTT (protocolo padronizado do lab)
                 →  ReqValLive (SC pré-aprovados no gate)
                 →  Laudo PASS/FAIL + momentos críticos
                 →  Esqueleto SysML v2 (opcional para o projeto)
```

**Sucesso mínimo da dissertação:** ≥2 tipos de Success Criteria (ex.: métrica por drone + métrica agregada entre drones) avaliados em corridas reais no lab, com laudo coerente com a telemetria e esqueleto SysML gerado.

### 9.2 Extensão (desejável) — SARITA / CET-ADS

```text
Antes
  Projeto CET-ADS_i  →  requisitos (Markdown)
                     →  gate ACCEPT/REJECT
                     →  payload conforme protocolo MQTT padronizado (uniforme)

Durante
  Telemetria da demo  →  sessão ReqValLive
                      →  evidência (atual, mínimo, 1ª violação, falhas)

Depois
  Laudo PASS/FAIL + momentos críticos
  Esqueleto SysML v2 (partida MBSE, não simulação Magic)
```

**Sucesso do ensaio SARITA (se ocorrer):** ≥1 projeto completa o ciclo; desejável 2+ sob o mesmo contrato MQTT.

O WARA-PS permanece apenas como **referência de motivação** (arenas multiagente), não como meta.

---

## 10. Critérios de conclusão da dissertação

1. Método do gate e da evidência live **descrito e justificado** (Methods + papel de métricas no ADS-VD).
2. PoC cobre o ciclo completo para pelo menos **dois tipos de SC** (por entidade + agregada, ou equivalente).
3. Avaliação empírica **obrigatória** com drones reais / MQTT no CONCEPTIO.
4. SARITA documentado **apenas se ocorrer** — ausência não impede a conclusão.
5. Limitações explícitas: escala lab; SysML = esqueleto; sem overclaim de simulação Magic.
6. Artefatos reproduzíveis (código, exemplos, laudos, referência ao protocolo MQTT do lab).

---

## 11. Riscos residuais (aceitos e mitigados)

| Risco | Mitigação |
|-------|-----------|
| SARITA não ocorre | PoC e conclusão assentadas no CONCEPTIO (drones reais + MQTT) |
| Heterogeneidade de payload | No lab e no SARITA: **protocolo MQTT padronizado** / payloads uniformes |
| Condições de voo / janela operacional | Missões de teste planejadas; repetir corridas; combinar com fixture quando necessário para regressão |
| LLM gera SC fracos | Gate independente do LLM; SC também via JSON / exemplos |
| Expectativa errada sobre SysML | Claim fixo: esqueleto para não começar do zero; V&V live está no ReqValLive |

Com as premissas acima, **não há risco estrutural** que invalide o mestrado.

---

## 12. Estrutura sugerida dos capítulos

1. Introdução (problema, objetivos, escopo, organização)
2. Fundamentação (V&V, Success Criteria, MBSE/SysML, ADS-VD / CET-ADS, protocolo MQTT do lab)
3. Trabalhos relacionados e gap (simulação vs live; demos sem SC)
4. Método proposto (gate, evidência temporal, ciclo lab / SARITA)
5. Implementação ReqValLive (arquitetura, alinhamento ao MQTT padronizado, gerador de esqueleto SysML)
6. Experimentos e resultados (CONCEPTIO obrigatório; SARITA se houver)
7. Discussão
8. Conclusões e trabalhos futuros

---

## 13. Frase de posicionamento (para banca / resumo)

> Esta dissertação desenvolve e avalia uma prova de conceito para validação live de Success Criteria em missões multiagente no laboratório CONCEPTIO (contexto CET-ADS): critérios são aprovados ou recusados antes da run; drones reais publicam telemetria em MQTT padronizado durante missões de teste; o sistema devolve laudo PASS/FAIL com momentos críticos e um esqueleto SysML v2 para reuso MBSE — sem pretender simulação funcional no CATIA Magic nem escala industrial. O evento SARITA, se realizado, é extensão natural sob o mesmo protocolo uniforme.
)
