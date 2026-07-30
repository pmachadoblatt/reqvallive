# CONTEXTO OBRIGATÓRIO — CATIA / SysML v2 (ler antes de qualquer plano CATIA)

**Última revisão:** 2026-07-30  
**Estado validado no lab:** projeto real SysML v2 + export Magic testado no ReqValLive.

Este ficheiro existe porque já houve um erro caro: planear **Excel/CSV Sync** como
caminho principal de UPDATE, quando o ambiente real é **SysML v2 tabular views** —
onde esse Sync **não aparece / não é o fluxo v1**.

---

## Ambiente real (não assumir v1)

| Item | Valor no mestrado CONCEPTIO |
|------|------------------------------|
| Produto | CATIA Magic / Magic Systems of Systems Architect |
| Versão alvo | **2026x** (SysML v2) |
| Metamodelo | **SysML v2** (não SysML v1 Requirement Table clássica) |
| Vista típica | `view ModelTable` / tabular view dinâmica (`Documentation Body`, `Req ID`, `Declared Name`) |
| Export entrada | **File → Export To → SysML v2 Textual Notation** → `.sysml` |
| Import `.sysml` de volta | Cria **namespace raiz separado** — **não** edita o modelo aberto |
| Colaboração | Collaborate → **Teamwork Cloud**; REST SysML v2 no servidor (evolução) |

**Proibido ao agente:** responder sobre “atualizar o CATIA” assumindo tabela de
requisitos SysML **v1** ou Excel/CSV Sync como default, sem reler este ficheiro e
`docs/CATIA_UPDATE_FORMATOS.md`.

---

## O que o usuário vê (e por que parece “só um texto”)

O padrão do orientador (Betina/Falqueto / `_go_to_verification`) usa o campo
**Documentation / doc** como **marcador parseável**, não como UI rica de V&V.

Por isso colar:

```text
_verification_FAIL
_go_to_verification
metric: batteryLevel
...
```

no **Documentation Body**:

- **é** o contrato textual combinado (máquina + engenheiro leem tags);
- **não** cria botão PASS/FAIL no Magic;
- **não** mostra o Success Criteria como colunas estruturadas na tabela;
- o laudo visual PASS/FAIL com evidência vive no **Relatório HTML do ReqValLive**.

Expectativa errada: “Magic vira dashboard de verificação”.  
Expectativa correta MVP: “Magic guarda estado de verificação no `doc`; ReqValLive mede e lauda”.

---

## Canais de UPDATE — realidade 2026-07-30

| Canal | SysML v2 2026x (nosso caso) | Notas |
|-------|-----------------------------|--------|
| Colar / escrever **Documentation** | Funciona (manual ou plugin) | MVP demo; parece “só texto” — é intencional no contrato `doc` |
| Excel/CSV Sync | **Não contar como caminho principal** | Docs oficiais ainda referem sync em tabelas estilo **SysML v1**; na view tabular v2 o botão pode **não existir** |
| Import `.sysml` update | **Não** atualiza o aberto | Namespace novo |
| Plugin Open API | Sim (desktop) | `setDocumentation` / atributos — trabalho médio |
| **REST SysML v2 (TWC)** | Sim (servidor) | Evolução recomendada no lab (Collaborate já existe) — ver `docs/LEMBRETE_TWC_REST_EVOLUCAO.md` |

---

## Checklist antes de propor qualquer feature CATIA

1. Confirmar: estamos em **SysML v2 / 2026x**? (sim, salvo o usuário dizer o contrário)
2. Abrir este ficheiro + `docs/CATIA_UPDATE_FORMATOS.md` + `docs/LEMBRETE_TWC_REST_EVOLUCAO.md`
3. Pesquisar docs **SYSML2P / 2026x**, não só MD2021x / Requirement Table v1
4. Distinguir: **gate OK/NOK** (antes de medir) ≠ **PASS/FAIL da medição** (depois)
5. Distinguir: **laudo ReqValLive** (UI) ≠ **marcador no `doc` Magic** (texto)
6. Se a proposta for CSV Sync: dizer explicitamente que é **legado / v1 / incerto no v2** e oferecer REST/plugin/paste

---

## Onde está a “verdade” da corrida

- Gate + SC aprovado + evidência + FAIL latch → **sessão ReqValLive + relatório HTML**
- Tags `_verification_*` no Magic → **rastreio no modelo**, não substituto do laudo
- JSON / CSV gerados → **pacote de transferência**; CSV não é o produto final no v2

---

## Frase curta para não esquecer

> Ambiente = **Magic 2026x + SysML v2**. CSV Sync ≠ caminho garantido. Documentation = marcadores. Laudo = ReqValLive. Fecho automático futuro = **REST TWC** ou plugin.
