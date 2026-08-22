# Alinhamento PoC × orientador × V&V — pronto para escrita?

**Data:** 2026-08-22  
**Contexto:** após UI EN, laudo de procedimento, rate/dwell, VerificationResult legível, LLM só opcional.

---

## 1. O que o orientador pediu (ago/2026) vs estado

| Pedido / entrega | Estado | Nota |
|------------------|--------|------|
| Ciclo SysON → gate → MQTT → laudo → write-back | **Feito e demonstrado** | Aceite na reunião 03/08 |
| Jefferson / naturezas GSE | **Parcial (4/7)** | valor, amplitude, **rate**, **dwell**; resto = futuro honesto |
| Esqueleto de capítulos (ITA / DSR) | **Feito** | `latex/` — escopo; prosa ainda a escrever |
| UI em inglês + limpar CATIA da face | **Feito** | CATIA/Markdown em Advanced; Help drawer |
| MQTT “online” / `concept/...` / RPS | **Aguardando** | Não bloqueia escrita; ver `MQTT_AGUARDANDO_ORIENTADOR.md` |
| VerificationResult no diagrama SysON | **Opcional P2** | Explorador + arrastar — suficiente |

**Conclusão orientador:** o “desespero” (provar que o ciclo existe) **já passou**. Daqui: enriquecer medição (feito o essencial) + **escrever**.

---

## 2. Alinhamento com V&V (SIS-08 Methods / MSFC)

| Princípio SE | Materialização no ReqValLive |
|--------------|------------------------------|
| SC aprovável **antes** da atividade de V&V | Gate ACCEPT/REJECT + bloqueio de start |
| Método coerente com evidência | `vv_method=test` + MQTT live |
| Evidência temporal honesta | Latch FAIL; min/max; 1ª violação; rate/dwell |
| Laudo auditável | HTML com procedimento, topic, janela, snapshot SC |
| Rastreabilidade requisito ↔ evidência ↔ modelo | Import SysON + `VerificationResult_PASS/FAIL` |
| Configuração do critério da corrida | `approved_sc_snapshot` congelado no start |
| Honesty MBSE | Disclaimer: esqueleto SysML ≠ simulação Magic |

Lacunas **não bloqueantes** para o claim da PoC: Environment/Restrictions/Checkpoints mais ricos (P1); timeline de violações mais densa (P1); pacote export único (P1).

---

## 3. LLM — papel correto para a dissertação

| Uso | Status |
|-----|--------|
| Publish SysON | **Determinístico** (rápido) |
| Narrativa da missão | **Opcional** — botão *LLM narrative* após Stop |
| Markdown → requisitos | Advanced (não é o fluxo da tese) |
| UPDATE CATIA | Advanced / legado |

O veredicto PASS/FAIL **nunca** depende do LLM. Narrativa = comunicação, não prova.

---

## 4. Pode partir para a escrita?

**Sim — para o artefacto / PoC.** O software já sustenta o claim de Engenharia de Sistemas da dissertação (ciclo fechado + SC + evidência + laudo + write-back).

### O que a escrita ainda exige (trabalho acadêmico, não “código faltando”)

1. **Cap. II — literatura / mapeamento**  
   Não precisa SLR “gigante” no primeiro draft, mas **precisa** de protocolo explícito (perguntas, bases, inclusão/exclusão, síntese). O orientador espera rigor; reserve tempo para isso **em paralelo** à redação de Resultados.

2. **Cap. IV — Resultados**  
   Colar ensaio documentado (`ENSAIO_SYSON_RATE_DWELL.md`) + capturas do projeto Sabonete + tabela PASS/FAIL + ameaças à validade. Corrigir qualquer texto que ainda diga que rate/dwell são futuro.

3. **Cap. I / III / V**  
   Revisar tom (pt-BR acadêmico); Jefferson como vocabulário do método; conclusão **depois** dos resultados reais.

4. **Escopo honesto**  
   Declarar: 4/7 naturezas Jefferson; MQTT WARA-PS = futuro; SARITA = pós-mestrado.

### O que **não** precisa esperar para começar a escrever

- Adaptador WARA-PS  
- Aparecer sozinho no diagrama SysON  
- Jefferson 5–7  
- Renomear o app  

---

## 5. Checklist “PoC fechada o bastante”

| # | Critério FEATURES_MESTRADO_SE | OK? |
|---|------------------------------|-----|
| A | Gate antes da run | Sim |
| B | REJECT com dimensão SE | Sim |
| C | Veredicto temporal fiel | Sim (+ rate/dwell) |
| D | Laudo: exigido / medido / passou / quando | Sim |
| E | Ponte MBSE honesta | Sim |
| F | Ciclo CONCEPTIO / MQTT | Sim (ensaio + lab) |
| G | Limites documentados | Sim (este doc + FEATURES) |

---

## 6. Recomendação prática

1. **Congelar** a PoC neste estado para a dissertação (só bugs críticos).  
2. **Começar a escrever** Cap. IV (mais fácil: evidência já existe) e Cap. II (protocolo SLR/mapeamento).  
3. Manter MQTT `concept/...` e polish extra como **fase pós-rascunho** ou entrega Christopher em paralelo, sem bloquear o texto.

**Veredicto:** alinhado ao proposto pelo orientador e às referências de V&V usadas no projeto; **apto a partir para a escrita**, com a ressalva de que a qualidade da dissertação virá do rigor bibliográfico e da narrativa dos experimentos — não de mais features no app.
