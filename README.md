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

### Configuração (`.env`)

1. Copie o exemplo:
   ```bash
   copy .env.example .env
   ```
2. Edite `.env` e preencha pelo menos:
   ```env
   GITHUB_TOKEN=seu_token_aqui
   REPO=fastapi/typer
   OFFLINE=false
   MAX_ISSUES=0
   MAX_PULLS=0
   ```

O `main.py` **carrega o `.env` automaticamente** ao iniciar. Você **não precisa** exportar o token no terminal se ele já estiver no `.env`.

> **Importante:** o arquivo `.env` não vai para o GitHub (está no `.gitignore`). Nunca commite seu token.

Crie o token em: https://github.com/settings/tokens (escopo `public_repo` ou `repo`).

### 1) Modo offline (sem token — para testar)

No `.env`, use `OFFLINE=true`, ou rode:

```bash
python main.py --offline
```

Gera em `output/` os `.graphml` e `metricas_integrado.json`.

### 2) Mineração real do Typer

Com o `.env` configurado, basta:

```bash
python main.py
```

O script usa os valores do `.env` (`GITHUB_TOKEN`, `REPO`, `MAX_ISSUES`, `MAX_PULLS`, etc.).

**Alternativa:** definir o token só na sessão atual do terminal (sobrescreve o `.env`):

```powershell
$env:GITHUB_TOKEN = "seu_token_aqui"
python main.py
```

Use `MAX_ISSUES=0` e `MAX_PULLS=0` no `.env` para minerar tudo. Em repositórios grandes, isso pode levar bastante tempo e consumir muitas chamadas de API.

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
- Com `GITHUB_TOKEN` no `.env`, rode apenas `python main.py`.
- Sem token, use `OFFLINE=true` no `.env` ou `python main.py --offline`.
- Resultados reutilizáveis ficam em cache: `output/interactions_cache.json`.
