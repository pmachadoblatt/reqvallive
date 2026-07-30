# Formatos de UPDATE CATIA — o que atualiza o modelo aberto

> **Ler primeiro:** [`CONTEXT_OBRIGATORIO_CATIA.md`](CONTEXT_OBRIGATORIO_CATIA.md).  
> Ambiente real do mestrado: **Magic 2026x + SysML v2**.  
> **Correção 2026-07-30:** Excel/CSV Sync **não** é o caminho principal na view tabular SysML v2
> (o botão pode não existir). Docs oficiais de Sync ainda falam em tabelas estilo **SysML v1**.

**Pergunta crítica:** gerar um ficheiro no ReqValLive e “mandar de volta” atualiza o
projeto **já aberto** no CATIA Magic / Cameo?

## Conclusão (docs oficiais + teste real no lab)

| Canal | Lê no Magic? | Atualiza o modelo **já aberto**? | Notas |
|-------|--------------|----------------------------------|-------|
| Colar / escrever **Documentation** | Sim | **Sim** (manual) | MVP atual; é texto/marcadores, **não** UI PASS/FAIL |
| **Excel/CSV Sync** | Em tabelas clássicas | Em v1: sim; **em view tabular SysML v2: não contar** | Não apareceu na ModelTable v2 do lab |
| **Plugin Java Open API** | N/A (in-process) | **Sim** | Caminho desktop “sozinho” |
| **SysML v2 REST API** (TWC) | Via servidor | **Sim** no projeto no servidor | Evolução recomendada (lab tem Collaborate) |
| **Import SysML v2 Textual Notation (`.sysml`)** | Sim | **Não** — namespace raiz separado | Não substitui o aberto |

Fontes:

- [Textual notation import/export](https://docs.nomagic.com/SYSML2P/2026x/textual-notation-import-export-254422195.html) — *“imported into a separate root namespace”*
- [Excel/CSV Sync](https://docs.nomagic.com/MT/2026x/magic-cyber-systems-engineer---cameo-systems-modeler/sync-with-excel-or-csv-files-272733849.html) — sync em tabelas; conclusão no lab: **não usar como default v2**
- [Modeling Tools Developer Guide / Open API](https://docs.nomagic.com/DEVG/latest/modeling-tools-developer-guide-303988912.html)
- [SysML v2 REST API no TWC 2026x](https://docs.nomagic.com/SYSML2P/2026x/catia-magic-cameo-sysml-v2-solution-272740940.html)
- Lab: `docs/LEMBRETE_TWC_REST_EVOLUCAO.md`, `docs/CONTEXT_OBRIGATORIO_CATIA.md`

## Implicação para o mestrado

**Não adianta** tratar o `.sysml` gerado como “UPDATE dinâmico do modelo aberto”.
O Magic **importa** textual SysML v2 para um namespace **novo**, não faz merge in-place
nos requisitos que o engenheiro já tem abertos.

**Também não adianta** prometer que colar no Documentation Body “mostra FAIL como produto”
no Magic: o contrato do `doc` é **marcador textual**; o laudo visual é o **HTML do ReqValLive**.

Para o ciclo **dinâmico** (objetivo final: CATIA atualiza sozinho) em **SysML v2**:

1. **Agora (MVP):** ReqValLive mede + laudo HTML; tags `_verification_*` no `doc` (colar ou gerar pacote).  
2. **Evolução recomendada no CONCEPTIO:** cliente **REST SysML v2** no Teamwork Cloud.  
3. **Alternativa desktop:** plugin Open API (`plugin_bridge` no JSON).  
4. **CSV Sync:** só se validado numa tabela clássica; **não** é o plano default v2.

O `.sysml` atualizado continua como **arquivo / diff** — com disclaimer explícito.  
O CSV continua gerado como pacote auxiliar, sem overclaim de Sync no v2.

## Formato CSV (ReqValLive → Magic Sync)

Colunas (cabeçalho na 1.ª linha, UTF-8 BOM para Excel):

| Coluna | Uso no Magic |
|--------|----------------|
| `Id` | Identification Property (requirements) |
| `Name` | Nome do requirement |
| `Documentation` | Texto completo do `doc` / Documentation (tags `_verification_*`) |
| `VerificationTag` | Coluna auxiliar (mapear só se existir na tabela; senão ignorar) |

Conteúdo de `Documentation` = bloco `catia_doc_append` (ou `catia_doc_llm` se LLM).

### Passos no Magic (projeto aberto)

1. Abrir / criar tabela de requisitos com colunas **Id**, **Name**, **Documentation**.
2. Excel/CSV Sync → Select File → escolher `verification_sync.csv` do ReqValLive.
3. Identification Property = **Id** (ou Default para requirements).
4. Mapear `Documentation` ↔ coluna Documentation.
5. **Read From File** — elementos existentes com o mesmo Id são **atualizados**.

## Formato `.sysml` (arquivo, não in-place)

- Parte do export original da sessão (`source_markdown` / export CATIA).
- Substitui o `doc /* … */` dos requisitos medidos pelas tags de verificação.
- Import no Magic = **novo** namespace — comparar / copiar, **não** sync do aberto.

## Contrato futuro do plugin (`plugin_bridge`)

JSON em `verification_update.json` → secção `plugin_bridge`:

```json
{
  "protocol": "reqvallive.catia.plugin.v1",
  "actions": [
    {
      "op": "set_documentation",
      "element_name": "RQ_BAT_001",
      "documentation": "_verification_FAIL\n..."
    }
  ]
}
```

O plugin Java deve: localizar NamedElement por nome/Id → `SessionManager.createSession`
→ `setDocumentation` → `closeSession`.

## Tags no `doc` (Christopher / Betina–Falqueto)

Mantidas no texto de Documentation:

- `_go_to_verification` — continua elegível para re-medir
- `_verification_PASS` / `_verification_FAIL` / `_verification_INCONCLUSIVE`
