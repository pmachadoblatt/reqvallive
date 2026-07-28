# Formatos de UPDATE CATIA — o que atualiza o modelo aberto

**Pergunta crítica:** gerar um ficheiro no ReqValLive e “mandar de volta” atualiza o
projeto **já aberto** no CATIA Magic / Cameo?

## Conclusão (docs oficiais Dassault / No Magic)

| Canal | Lê no Magic? | Atualiza o modelo **já aberto**? | Notas |
|-------|--------------|----------------------------------|-------|
| **Excel/CSV Sync** (tabela de requisitos) | Sim | **Sim** — identifica por **Id**/Name e atualiza propriedades existentes | Mecanismo nativo bidirecional |
| **Plugin Java Open API** (`SessionManager` + `setDocumentation`) | N/A (in-process) | **Sim** — edição dinâmica real | Caminho do objetivo final “sozinho” |
| **SysML v2 REST API** (Teamwork Cloud / Magic Collaboration Studio) | Via servidor | **Sim** no projeto no servidor; MagicLab reflecte mudanças | Requer TWC; não é ficheiro local solto |
| **Import SysML v2 Textual Notation (`.sysml`)** | Sim | **Não** — cria um **namespace raiz separado** | Não substitui elementos do modelo aberto |
| Colar texto no campo Documentation | Sim | Sim (manual) | MVP atual sem sync |

Fontes:

- [Textual notation import/export](https://docs.nomagic.com/SYSML2P/2026x/textual-notation-import-export-254422195.html) — *“imported into a separate root namespace”*
- [Excel/CSV Sync](https://docs.nomagic.com/MT/2026x/magic-cyber-systems-engineer---cameo-systems-modeler/sync-with-excel-or-csv-files-272733849.html) — sync atualiza elementos existentes por Identification Property (Id em requirements)
- [Modeling Tools Developer Guide / Open API](https://docs.nomagic.com/DEVG/latest/modeling-tools-developer-guide-303988912.html) — único caminho in-process sem TWC
- [SysML v2 REST API no TWC 2026x](https://docs.nomagic.com/SYSML2P/2026x/catia-sysml-v2-solution-272740940.html) — create/edit/query via API standard

## Implicação para o mestrado

**Não adianta** tratar o `.sysml` gerado como “UPDATE dinâmico do modelo aberto”.
O Magic **importa** textual SysML v2 para um namespace **novo**, não faz merge in-place
nos requisitos que o engenheiro já tem abertos.

Para o ciclo **dinâmico** (objetivo final: CATIA atualiza sozinho):

1. **Curto prazo (agora):** export **CSV** no formato Excel/CSV Sync → o engenheiro
   faz *Read From File* na tabela de requisitos ligada ao ficheiro → Documentation
   dos `RQ_*` existentes é atualizada **no projeto aberto**.
2. **Médio prazo:** plugin Magic (Open API) que lê `verification_update.json` /
   CSV da pasta watch e chama `setDocumentation` em sessão.
3. **Com TWC:** cliente REST SysML v2 no ReqValLive (fora do MVP de lab local).

O `.sysml` atualizado continua a ser gerado como **arquivo / diff / reimport em
sandbox** — útil para auditoria e para quem não usa Sync — com disclaimer explícito.

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
