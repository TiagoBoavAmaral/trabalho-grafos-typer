# Trabalho Prático — Teoria de Grafos (PUC Minas)

Ferramenta para minerar colaboração no repositório **[fastapi/typer](https://github.com/fastapi/typer)** (~19,5k estrelas), modelar grafos de interação e calcular métricas de redes.

## Estrutura

| Pasta / arquivo | Conteúdo                                                    |
| --------------- | ----------------------------------------------------------- |
| `mining/`       | Etapa 1 — coleta GitHub e construção dos 4 grafos           |
| `graph/`        | Etapa 2 — `AbstractGraph`, matriz, lista, exportação Gephi  |
| `analysis/`     | Etapa 3 — centralidades, densidade, clustering, comunidades |
| `main.py`       | Pipeline completo (minerar → grafos → métricas → export)    |
| `demo_app.py`   | Demo da API de grafos (Etapa 2)                             |
| `tests/`        | Testes unitários                                            |

## Grafos gerados (modelagem)

1. **Grafo 1** — comentários em issues/PRs
2. **Grafo 2** — fechamento de issues
3. **Grafo 3** — revisões/aprovações/merges de PRs
4. **Grafo integrado** — pesos: comentário=2, issue comentada=3, revisão=4, merge=5

Cada usuário GitHub é um vértice; arestas direcionadas `origem → alvo`.

## Como executar

### Usando `.env`

Copie `.env.example` para `.env` e preencha `GITHUB_TOKEN` se quiser minerar com a API do GitHub.

### 1) Modo offline (sem token — para testar)

```bash
python main.py --offline
```

Gera em `output/` os `.graphml` e `metricas_integrado.json`.

### 2) Mineração real do Typer

1. Crie um [Personal Access Token](https://github.com/settings/tokens) (escopo `public_repo` ou `repo`).
2. No PowerShell:

```powershell
$env:GITHUB_TOKEN = "seu_token_aqui"
python main.py --repo fastapi/typer --max-issues 0 --max-pulls 0
```

Use `0` para minerar tudo. Para repositórios grandes, isso pode levar bastante tempo e usar muitas chamadas de API.

### 3) Demo da API de grafos (Etapa 2)

```bash
python demo_app.py
```

### 4) Testes

```bash
python -m unittest discover -s tests -p "test*.py" -v
```

## Entrega (checklist do PDF)

- [ ] Código fonte (este repositório)
- [ ] Relatório LaTeX (template SBC) — descrever escolha do Typer, modelagem, resultados e telas
- [ ] PDF do relatório
- [ ] `.zip` com código + `.tex` + PDF
- [ ] Indicar no relatório o que cada integrante fez
- [ ] Vídeo (5–10 min) e apresentação oral (10–15 min)
- [ ] Importar `output/grafo_integrado.graphml` no **Gephi** para figuras do relatório

## Observações

- Não usa `networkX` nem bibliotecas prontas de grafos.
- Sem `GITHUB_TOKEN`, use `--offline` ou dados em cache (`output/interactions_cache.json`).
