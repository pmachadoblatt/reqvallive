# Contrato SysON — Documentation vs Success Criteria

**Decisão (2026-07-30, alinhada ao Pedro):**  
- **Documentation** = só `_go_to_verification` (seleção para V&V). **Sem** copy-paste de laudo.  
- **Success Criteria** = **elementos do modelo** no SysON (aparecem no explorador / diagrama).  
- **Resultado da medição** = item `VerificationResult` **filho de cada requirement** (status, reason, failedAt, extreme…).  
- **ReqValLive** = interpreta o que vem do SysON; **não** inventa o critério; LLM enriquece reason/evidence antes de escrever.

## Divisão de responsabilidades

| Onde | O quê |
|------|--------|
| SysON — Documentation | Só `_go_to_verification` (nunca o laudo) |
| SysON — modelo (atributos / item aninhado) | Success Criteria visível |
| SysON — item `VerificationResult` sob cada RQ | PASS/FAIL + motivo + quando + extremos |
| ReqValLive | Lê marcador + SC → gate → MQTT → laudo HTML → **insere** VerificationResult via GraphQL |

Isto combina com o orientador: o `doc` é **seleção** para verificação, não o sítio do critério mensurável.

## Padrão no SysON (authoring)

### 1) Documentation (campo Documentation do requisito)

```text
_go_to_verification
```

Nada mais (sem JSON, sem métrica).

### 2) Success Criteria no modelo (aparece sob o requisito)

Usar um **item aninhado** `SuccessCriteria` com atributos — fica explícito no explorador:

```sysml
requirement RQ_01 {
    doc /*
    _go_to_verification
    */

    item SuccessCriteria {
        attribute scType = "threshold";
        attribute metric = "batteryLevel";
        attribute operator = ">=";
        attribute value = 20.0;
        attribute unit = "percent";
        attribute scope = "all_entities";
        attribute tolerance = 0.0;
    }
}
```

**Alternativa** (mesmos nomes como atributos diretos do requirement):

```sysml
requirement RQ_01 {
    doc /* _go_to_verification */
    attribute scType = "threshold";
    attribute metric = "batteryLevel";
    attribute operator = ">=";
    attribute value = 20.0;
    attribute unit = "percent";
    attribute scope = "all_entities";
}
```

### Valores de `scType`

| scType | Atributos pedidos |
|--------|-------------------|
| `threshold` | metric, operator, value, unit?, scope?, tolerance? |
| `range` | metric, min_value, max_value, unit?, scope? |
| `statistical` | metric, aggregation (`range`/`max`/`min`), operator, value, unit? |

## Depois da medição — item `VerificationResult` (não Documentation)

O Documentation **permanece** só com `_go_to_verification`.

O resultado live é um **item** SysML v2 filho do requirement (categoria Structure / `ItemUsage`),
ligado ao RQ — com vários requisitos, cada um tem o seu bloco:

```text
RQ_01
  ├── scType / metric / …                    (Success Criteria — authoring)
  └── VerificationResult_FAIL_min18_…        (resultado — nome já mostra o veredicto)
        ├── Documentation: status, reason, failedAt, extreme…
        ├── attribute status = "FAIL"
        ├── attribute reason / failedAt / extremeValue / …
```

O explorador SysON só mostra o **nome** do item por defeito — por isso o app usa um nome
visível (`VerificationResult_FAIL_min18_batteryLevel_<sessão>`). Seleccione o item para ler
o Documentation resumido; expanda para os atributos.

Escrita automática via GraphQL `insertTextualSysMLv2` sob o requirement (validado na API REST).
Antes de escrever, o LLM (se disponível) enriquece `reason` e `evidenceSummary`.

**Não** usar copy-paste no Documentation do requisito para o laudo.

## O que o app faz

1. Lista requisitos com `_go_to_verification` no Documentation.  
2. Lê `SuccessCriteria` (item ou atributos) via API / export `.sysml`.  
3. Se faltar SC no modelo → gate **REJECT** (mensagem: definir SC no SysON) — **não** preenche no app.  
4. Mede → (opcional LLM) → cria/atualiza item `VerificationResult` **ligado** a cada RQ. Documentation **não** muda.

## Como criar na UI do SysON (o que estás a ver)

**Não** procures “Success Criteria” em Requirements. Não existe esse tipo.
Usa a categoria **Structure**.

### Caminho recomendado (mais simples): atributos no próprio RQ_01

1. No explorador ou no diagrama, **seleciona** o requisito `RQ_01`.
2. Abre a ferramenta contextual (a lista com Requirements / Structure / …).
3. Clica **Structure** (não Requirements).
4. Clica **New Attribute** (repete para cada campo abaixo).
5. Seleciona cada atributo → **F2** (ou editar o rótulo) e escreve, por exemplo:

| Texto a escrever no atributo (direct-edit) | Significado |
|--------------------------------------------|-------------|
| `scType = "threshold"` | tipo do critério |
| `metric = "batteryLevel"` | métrica MQTT |
| `operator = ">="` | operador |
| `value = 20.0` | limiar |
| `unit = "percent"` | unidade |

> O F2 grava essa string como **nome** do atributo (não como FeatureValue). O ReqValLive
> aceita esse padrão (`metric = "batteryLevel"` no declaredName).
| `scope = "all_entities"` | âmbito |

6. Documentation do `RQ_01` = só:

```text
_go_to_verification
```

No explorador deves ver algo como:

```text
RQ_01
  ├── scType
  ├── metric
  ├── operator
  ├── value
  ├── unit
  └── scope
```

### Alternativa: item `SuccessCriteria` (também em Structure)

1. Seleciona `RQ_01`.
2. **Structure → New Item** (se aparecer; por vezes “New Item Usage”).
3. Renomeia o item para `SuccessCriteria` (F2).
4. Seleciona esse item → **Structure → New Attribute** e cria os mesmos atributos.

### Se preferires colar texto (sem clicar atributo a atributo)

1. Clica com o botão direito em `RQ_01` (ou no Package).
2. Procura **New objects from text** / **Insert textual SysML**.
3. Cola:

```sysml
attribute scType = "threshold";
attribute metric = "batteryLevel";
attribute operator = ">=";
attribute value = 20.0;
attribute unit = "percent";
attribute scope = "all_entities";
```

## Por que o import do `reqvallive_demo.sysml` “não carregou”

No SysON o ficheiro **não** se abre como “Abrir projeto”. O fluxo correcto:

1. Na página inicial / projeto: **Upload model** / **Import** → escolher o `.sysml`  
   (cria um **documento/modelo novo** no explorador — não substitui o ReqTest automaticamente).
2. Ou, dentro do ReqTest: **New objects from text** no Package e colar o conteúdo do demo.

Se o upload falhar: erros comuns são dependências em falta ou sintaxe que a v2025.6 ainda não importa por completo. Nesse caso usa o caminho **Structure → New Attribute** acima (é o oficial nos tutoriais SysON).

## Depois de criado

No ReqValLive → SysON → **Importar do SysON**.  
O app lê Documentation (`_go_to_verification`) + atributos `metric` / `operator` / `value` / …
