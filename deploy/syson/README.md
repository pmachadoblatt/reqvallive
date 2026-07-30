# SysON local (Docker) — lab e casa

Editor web open-source de modelos SysML v2. No mestrado é o **anfitrião do modelo**
enquanto o servidor de colaboração do laboratório estiver bloqueado.

| Item | Valor |
|------|--------|
| Versão imagem | `eclipsesyson/syson:v2025.6.0` |
| URL no PC | http://localhost:8081 |
| App ReqValLive | http://localhost:8080 (porta diferente de propósito) |
| Perfil | single-user, sem login |

## Pré-requisito

Docker Desktop instalado e a correr.

## Subir / parar

```powershell
cd <repo-ReqValLive>
.\deploy\syson\up.ps1
# browser → http://localhost:8081

.\deploy\syson\down.ps1          # para; mantém projetos no volume
.\deploy\syson\down.ps1 -Wipe    # apaga também a base neste PC
```

Primeira execução descarrega imagens (~alguns minutos).

## Como usar o mesmo SysON no trabalho e em casa

Não há um contentor “na nuvem” partilhado. Há **a mesma receita no Git** e duas
formas de levar o progresso:

### 1) Fonte principal (recomendado): modelos em ficheiro no Git

1. No SysON: File → Export / download do modelo em notação textual (`.sysml`).
2. Guarde em `models/syson/` e faça `git commit` + `git push`.
3. Em casa: `git pull` → `.\deploy\syson\up.ps1` → Import do `.sysml` na UI.

Assim o trabalho continua **sem VPN** e sem depender da base Docker.

### 2) Opcional: backup da base Postgres

Se quiser levar projetos já criados na UI sem reimportar:

```powershell
# no PC de origem (SysON a correr)
.\deploy\syson\backup-db.ps1
# copie deploy/syson/backups/syson_pg_*.sql para o outro PC (pen/Drive)

# no PC de destino
.\deploy\syson\up.ps1
.\deploy\syson\restore-db.ps1 -File .\deploy\syson\backups\syson_pg_XXXX.sql
```

Os dumps `.sql` **não** vão para o Git (pasta `backups/` ignorada).

### O que o Git garante vs o que fica no PC

| Via Git (lab ↔ casa) | Só neste PC (volume Docker) |
|----------------------|-----------------------------|
| `deploy/syson/docker-compose.yml` + scripts | Projetos na UI até fazer backup/export |
| `models/syson/*.sysml` (quando existirem) | Volume `syson_pgdata` |

`docker compose down` **sem** `-Wipe` **não** apaga o volume deste PC.

## Checklist primeira vez

1. `.\deploy\syson\up.ps1`
2. Abrir http://localhost:8081
3. Criar um projeto de teste na UI
4. (Mais tarde) importar `models/syson/reqvallive_demo.sysml` quando existir

## Troubleshooting

| Sintoma | Acção |
|---------|--------|
| Porta 8081 ocupada | Edite `SYSON_HOST_PORT` em `deploy/syson/.env` |
| Docker não corre | Abra Docker Desktop e espere o motor ficar verde |
| App não abre após up | `docker compose -f deploy/syson/docker-compose.yml logs -f app` |
| Mac Silicon | `$env:DOCKER_DEFAULT_PLATFORM="linux/amd64"` antes do `up.ps1` |

Doc oficial: [local test](https://doc.mbse-syson.org/syson/v2025.6.0/installation-guide/how-tos/install/local_test.html).
