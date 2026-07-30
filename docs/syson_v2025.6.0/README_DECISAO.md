# SysON docs — leitura + decisão (atualizado 2026-07-30)

Fonte pedida pelo orientador:
https://doc.mbse-syson.org/syson/v2025.6.0/developer-guide/api.html

Espelho local nesta pasta (HTML + AsciiDoc + cookbook + OpenAPI).

---

## Critério do Pedro (alinhado com Christopher)

> Se o Christopher recomendou SysON, **não precisa ser CATIA**.  
> Se no SysON for **mais fácil de desenvolver**, é preferível.

Com isso, e **sem acesso à máquina Cassandra**, a decisão muda.

---

## Por que CONCEPTIO e Embry-Riddle deram o mesmo erro?

Não é porque os servidores “se conversam”. É **falha convergente** no mesmo produto:

1. **Mesma stack:** Magic Collaborate / Teamwork Cloud → grava modelos no **Apache Cassandra**.
2. **Criar projeto novo** faz um **import inicial grande** (szip / batch CQL). Editar projeto já existente costuma ser **delta** menor.
3. Cassandra tem um limite de segurança `batch_size_fail_threshold` (default clássico ~**50 KiB**). Se o batch do import ultrapassa → `InvalidQueryException: Batch too large` → `ImportFailedException`.
4. Docs da No Magic / Dassault para TWC pedem **subir** esses thresholds no `cassandra.yaml` do SO do servidor. Instalação “de fábrica” / Refresh / upgrade **2024x–2026x** + modelos **SysML v2** (mais pesados) → muitos sites batem nisto **sem se falarem**.
5. Por isso “de repente”: alguém tentou **Add/Create project** (ou Refresh trouxe o mesmo caminho de import) em dois sítios com **config Cassandra stock**. Mesmo bug de produto/defaults, servidores independentes.

**Sem acesso root ao Cassandra, não há fix vosso.** Pedir ao admin do lab é plano B; não é o caminho de desenvolvimento.

---

## Reavaliação CATIA/TWC vs SysON (facilidade)

| Critério | CATIA + TWC lab | SysON local (Docker) |
|----------|-----------------|----------------------|
| Criar modelo novo | Bloqueado (Cassandra) | Livre — vocês controlam o servidor |
| Acesso infra | Precisa admin CONCEPTIO / ERAU | `docker compose up` no PC |
| Auth REST | Ainda 401 / token confuso no lab | Localhost sem security no perfil test |
| API write UPDATE | Existe no Swagger TWC, mas auth+projeto bloqueiam | REST parcial + **file exchange** + GraphQL textual (docs) |
| Alinhamento orientador | Magic clássico | **Ele próprio mandou o link SysON** |
| Risco | Esperar admin / workaround projeto velho | API SysML v2 ainda incompleta; PoC open-source |

**Veredicto (com o critério novo):** para **desenvolver o fecho do ciclo** (app ↔ modelo ↔ UPDATE), **SysON é preferível agora**.  
CATIA/Magic continua útil como *authoring* opcional e para demos no lab, mas **não é o bloqueio** nem o alvo de API enquanto o Cassandra estiver inacessível.

Arquitetura PoC revista:

```text
SysON (modelo SysML v2 + API/file)
    ↕  .sysml / REST parcial / textual insert
ReqValLive (gate → GSE → MQTT → UPDATE)
```

Magic/TWC = paralelo / futuro se o admin corrigir Cassandra; não gate da tese.

---

## O que a doc SysON v2025.6.0 diz (ainda válido)

> API SysML v2 **isn’t fully available yet** → usar **file exchange**.

Mais recente (cookbook 2026.x): criar elementos via POST commits, GraphQL insert textual, download `.sysml`.  
Para ReqValLive, o caminho mais robusto no curto prazo é:

1. Subir SysON local (Docker).
2. Importar/criar o demo com `RQ_*` + `_go_to_verification` (UI ou `.sysml`).
3. ReqValLive continua a medir MQTT como hoje.
4. Fecho UPDATE: **re-export / patch `.sysml` + reimport**, ou spike REST/GraphQL se for estável — o que for mais simples no spike.

---

## Próximo passo concreto

1. ~~Instalar Docker / subir SysON~~ → `.\deploy\syson\up.ps1` → http://localhost:8081
2. ~~Modelo demo + cliente REST~~ → `models/syson/` + `python scripts/probe_syson.py` (vê ReqTest / RQ_01)
3. **Agora (UI):** colar `models/syson/RQ_01_documentation.txt` no Documentation do RQ_01
4. Spike UPDATE: patch `.sysml` + reimport (ou API se estável) + botão na UI

CATIA: só voltar a insistir em REST TWC quando houver projeto existente utilizável **ou** admin Cassandra.
