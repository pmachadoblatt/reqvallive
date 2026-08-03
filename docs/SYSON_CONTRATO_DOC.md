# Contrato SysON — Documentation vs Success Criteria

**Decisão (2026-07-30, alinhada ao Pedro):**  
- **Documentation** = só `_go_to_verification` (seleção para V&V). **Sem** copy-paste de laudo.  
- **Success Criteria** = **elementos do modelo** no SysON (aparecem no explorador / diagrama).  
- **Resultado da medição** = item `VerificationResult_*` **filho de cada requirement** (status, reason, failedAt, extreme…).  
- **ReqValLive** = interpreta o que vem do SysON; **não** inventa o critério; LLM enriquece reason/evidence antes de escrever.

**Validado:** casa 2026-07-30 · lab 2026-08 (E2E medir → publicar → modelo atualiza).

## Divisão de responsabilidades

| Onde | O quê |
|------|--------|
| SysON — Documentation | Só `_go_to_verification` (nunca o laudo) |
| SysON — modelo (atributos / item aninhado) | Success Criteria visível |
| SysON — item `VerificationResult_*` sob cada RQ | PASS/FAIL + motivo + quando + extremos |
| ReqValLive | Lê marcador + SC → gate → MQTT → laudo HTML → **insere** VerificationResult via GraphQL |

Isto combina com o orientador: o `doc` é **seleção** para verificação, não o sítio do critério mensurável.

## Pacote demo (multi-requisito)

Ficheiro: `models/syson/reqvallive_demo.sysml`

| Requirement | scType | Métrica | Expectativa com `publish_three_drones.py --mode both` |
|-------------|--------|---------|------------------------------------------------------|
| `RQ_BAT_001` / `RQ_01` | `threshold` | `batteryLevel >= 20` | **FAIL** (charlie sobe a partir de ~15%) |
| `RQ_ALT_BAND_001` | `range` | `altitudeAGL ∈ [20, 30]` | **PASS** (órbita ~24.5 ± span) |
| `RQ_ALT_VAR_001` | `statistical` | `altitudeAGL` agg=`range` `<= 1.0` | **FAIL** (span default 2.5 m) |
| `RQ_SEP_001` | `threshold` | `min_separation_m >= 20` | **PASS** (órbita raio 60 m) |

Objectivo do passo 2: **vários requisitos**, **três tipos de SC** no modelo, e no explorador SysON distinguir **PASS vs FAIL** só pelo nome do item (`VerificationResult_PASS_…` / `VerificationResult_FAIL_…`).

## Padrão no SysON (authoring)

### 1) Documentation (campo Documentation do requisito)

```text
_go_to_verification
```

Nada mais (sem JSON, sem métrica).

### 2) Success Criteria no modelo (aparece sob o requisito)

Usar um **item aninhado** `SuccessCriteria` com atributos — fica explícito no explorador:

```sysml
requirement RQ_BAT_001 {
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

| scType | Atributos pedidos | Exemplo no demo |
|--------|-------------------|-----------------|
| `threshold` | metric, operator, value, unit?, scope?, tolerance? | `RQ_BAT_001`, `RQ_SEP_001` |
| `range` | metric, min_value, max_value, unit?, scope? | `RQ_ALT_BAND_001` |
| `statistical` | metric, aggregation (`range`/`max`/`min`), operator, value, unit? | `RQ_ALT_VAR_001` |

#### Exemplo `range`

```sysml
item SuccessCriteria {
    attribute scType = "range";
    attribute metric = "altitudeAGL";
    attribute min_value = 20.0;
    attribute max_value = 30.0;
    attribute unit = "meters";
    attribute scope = "all_entities";
}
```

#### Exemplo `statistical` (peak-to-peak na janela de medição)

```sysml
item SuccessCriteria {
    attribute scType = "statistical";
    attribute metric = "altitudeAGL";
    attribute aggregation = "range";
    attribute operator = "<=";
    attribute value = 1.0;
    attribute unit = "meters";
}
```

## Depois da medição — item `VerificationResult` (não Documentation)

O Documentation **permanece** só com `_go_to_verification`.

O resultado live é um **item** SysML v2 filho do requirement (categoria Structure / `ItemUsage`),
ligado ao RQ — com vários requisitos, cada um tem o seu bloco:

```text
RQ_BAT_001
  ├── SuccessCriteria
  └── VerificationResult_FAIL_threshold_min15p2_batteryLevel_<sessão>

RQ_ALT_BAND_001
  ├── SuccessCriteria
  └── VerificationResult_PASS_range_min23p_altitudeAGL_<sessão>

RQ_ALT_VAR_001
  ├── SuccessCriteria
  └── VerificationResult_FAIL_statistical_…_altitudeAGL_<sessão>

RQ_SEP_001
  ├── SuccessCriteria
  └── VerificationResult_PASS_threshold_…_minseparationm_<sessão>
```

O explorador SysON só mostra o **nome** do item por defeito — por isso o app usa um nome
visível:

`VerificationResult_<PASS|FAIL>_<scType>_<extremo>_<métrica>_<sessão>`

Seleccione o item para ler o Documentation (`status`, `scType`, `reason`, …); expanda para os atributos.

Escrita automática via GraphQL `insertTextualSysMLv2` sob o requirement (validado na API REST).
Antes de escrever, o LLM (se disponível) enriquece `reason` e `evidenceSummary`.

**Não** usar copy-paste no Documentation do requisito para o laudo.

## O que o app faz

1. Lista requisitos com `_go_to_verification` no Documentation.  
2. Lê `SuccessCriteria` (item ou atributos) via API / export `.sysml`.  
3. Se faltar SC no modelo → gate **REJECT** (mensagem: definir SC no SysON) — **não** preenche no app.  
4. Mede → (opcional LLM) → cria/atualiza item `VerificationResult_*` **ligado** a cada RQ. Documentation **não** muda.

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
| `scope = "all_entities"` | âmbito |

> O F2 grava essa string como **nome** do atributo (não como FeatureValue). O ReqValLive
> aceita esse padrão (`metric = "batteryLevel"` no declaredName).

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
3. Cola o bloco `item SuccessCriteria { … }` do tipo desejado (threshold / range / statistical).

Ou importa o pacote completo: `models/syson/reqvallive_demo.sysml` (Upload model / Import).

## Por que o import do `reqvallive_demo.sysml` “não carregou”

No SysON o ficheiro **não** se abre como “Abrir projeto”. O fluxo correcto:

1. Na página inicial / projeto: **Upload model** / **Import** → escolher o `.sysml`  
   (cria um **documento/modelo novo** no explorador — não substitui o ReqTest automaticamente).
2. Ou, dentro do ReqTest: **New objects from text** no Package e colar o conteúdo do demo.

Se o upload falhar: erros comuns são dependências em falta ou sintaxe que a v2025.6 ainda não importa por completo. Nesse caso usa o caminho **Structure → New Attribute** acima (é o oficial nos tutoriais SysON).

## Checklist passo 2 (contrato endurecido)

1. Importar (ou recriar) os 4+ requisitos do demo no SysON.  
2. No ReqValLive → SysON → Importar → confirmar **threshold + range + statistical**.  
3. Com MQTT a publicar (`--mode both`), medir e **Publicar no SysON**.  
4. No explorador: sob cada RQ, um `VerificationResult_PASS_…` ou `VerificationResult_FAIL_…` sem abrir o item.

## Depois de criado

No ReqValLive → SysON → **Importar do SysON**.  
O app lê Documentation (`_go_to_verification`) + atributos `metric` / `operator` / `value` / `min_value` / `max_value` / `aggregation` / …
