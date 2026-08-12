# LaTeX — Dissertação ReqValLive (template ITA)

Fontes da dissertação para **Overleaf** / compilação local, versionadas neste monorepo.

## Template institucional

Usa a classe **`ita.cls`** (dissertação de mestrado: `\documentclass[msc]{ita}`),
do [Template Thesis ITA](https://github.com/gabriellnuness/Template_Thesis_ITA)
(também no [Overleaf](https://pt.overleaf.com/latex/templates/thesis-template-aeronautics-institute-of-technology-ita/yhfrqqydpygk)).

Alinhado ao [manual de dissertações/teses do ITA](http://www.ita.br/posgrad/tese)
(ABNT; espaçamento 1,5). Licença do template: `LICENSE-ITA-TEMPLATE`.

Estrutura de **conteúdo** (capítulos) segue o esqueleto DSR do orientador
(Chris Eng.ish): Introdução → Literatura → Metodologia → Resultados → Conclusão.

## Estrutura de pastas

```
latex/
  main.tex                 ← só configuração + \input (Overleaf: Main document)
  ita.cls + ita/           ← classe ITA
  biblatex-abnt/           ← estilo ABNT do template
  referencias.bib
  PreTextuais/             ← resumo, abstract, agradecimentos, listas
  capitulos/               ← um .tex por capítulo (com \chapter{})
    01-introducao.tex
    02-literatura.tex
    03-metodologia.tex
    04-resultados.tex
    05-conclusao.tex
  apendices/A-material-autor.tex
  anexos/A-material-apoio.tex
  figuras/
```

## Overleaf

1. **New Project → Import from GitHub** → repo `reqvallive`.
2. **Main document** = `latex/main.tex`.
3. Compiler: **pdfLaTeX** + **biber** (biblatex).
4. Completar em `main.tex`: programa oficial, nome completo do orientador, banca, datas, CDU.

## Compilação local

```powershell
cd latex
latexmk -pdf -interaction=nonstopmode main.tex
```

Requer TeX Live/MiKTeX com pacotes da classe `ita` (geometry, glossaries, biblatex, …).

## Relação com o app

| Pasta | Papel |
|-------|--------|
| `src/`, `deploy/`, … | Software ReqValLive |
| `latex/` | Texto do mestrado |

Não misturar código da PoC com capítulos.
