# Lembrete — Teamwork Cloud + REST SysML v2 (evolução)

**Data da conversa:** 2026-07-29 (casa)  
**Para:** puxar amanhã no trabalho e não esquecer o alinhamento.

---

## Contexto

O orientador quer o ciclo **Magic ↔ app** (enviar SC, medir, devolver OK/NOK).  
Discutimos um vídeo sobre **MCP + SysML v2 REST API** e se isso deveria substituir o fluxo atual.

**Conclusão:** não pivote o MVP. O caminho atual (ReqValLive + GSE + MQTT + CSV Sync / plugin) continua a base da dissertação.  
**REST via Teamwork Cloud** passa a ser **evolução viável**, porque o lab CONCEPTIO **já tem Collaborate / servidor** (projeto em equipe + acesso admin).

---

## O que é o quê (não confundir)

| Nome | Papel |
|------|--------|
| **Teamwork Cloud (TWC)** / Magic Collaboration Studio | **Servidor-repositório** de modelos; onde vive a **REST API SysML v2** |
| **Collaborate** (menu no Magic desktop) | Cliente a falar com o **TWC** |
| **Cameo / MagicLab Collaborator** | Portal **web** de revisão/comentários **em cima** do TWC (licença à parte) |

Ter **Collaborate** configurado + projeto partilhado + **admin** ≈ ter **TWC**. Collaborator ≠ TWC, mas costuma coexistir na mesma suíte.

---

## Posicionamento da dissertação

```text
AGORA (MVP / PoC)
  CATIA (req+SC) → .sysml / export
       → ReqValLive (gate → GSE → MQTT medição)
       → CSV Sync / JSON / .sysml arquivo → update OK/NOK

DEPOIS (evolução — lab tem TWC)
  ReqValLive ↔ REST SysML v2 no Teamwork Cloud
       → ler req/SC do projeto no servidor
       → escrever actualValue / Documentation / OK/NOK
       → Magic desktop / MagicLab reflectem o modelo no TWC
```

- **MCP + REST** (vídeo): produtividade LLM↔modelo no servidor — **trabalho futuro / DX**, não o núcleo V&V.  
- **Plugin Open API** no desktop: continua válido para update no modelo **aberto localmente**.  
- **REST no TWC**: update **no servidor** (o “conversar direto” com infraestrutura que vocês já têm).

Ver também: `docs/CATIA_UPDATE_FORMATOS.md`.

---

## Checklist rápido no trabalho (5 min)

1. No Magic: **Collaborate → Login** — anotar **host/URL** do servidor TWC.  
2. Abrir **Teamwork Cloud Admin** no browser (muitas vezes `https://<host>:8111`) com o user **admin**.  
3. Anotar **versão** do TWC / Magic (ideal **2026x** para API SysML v2 mais completa).  
4. Confirmar se existe projeto **SysML v2** no servidor (não só local).  
5. Procurar Swagger / docs da API SysML v2 no servidor (path tipicamente sob `/api/` ou similar — ver docs Dassault 2026x).  
6. Decisão: manter MVP ficheiro/CSV; planear **cliente REST** no ReqValLive como fase seguinte se a API responder.

---

## Frase para o orientador (se precisar)

> “O MVP mede e devolve evidência fora do runtime SysML v2 Simulation. Como o lab já tem Teamwork Cloud (Collaborate), a evolução natural para fecho automático no modelo é um cliente REST SysML v2 no ReqValLive — sem abandonar o GSE/MQTT como núcleo da validação live.”
