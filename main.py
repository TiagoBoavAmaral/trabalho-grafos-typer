from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from analysis import compute_metrics
from mining import InteractionExtractor, build_graphs_from_interactions
from mining.graph_factory import GraphSet


DEFAULT_REPO = "fastapi/typer"


def _print_top_users(graph_set: GraphSet, metrics, top_n: int = 10) -> None:
    idx_to_user = {i: u for u, i in graph_set.user_index.items()}
    g = graph_set.integrated_graph

    print("\n=== Métricas (grafo integrado) ===")
    print(f"Vértices: {g.getVertexCount()} | Arestas: {g.getEdgeCount()}")
    print(f"Densidade: {metrics.density:.4f}")
    print(f"Clustering: {metrics.clustering_coefficient:.4f}")
    print(f"Assortatividade: {metrics.assortativity:.4f}")
    print(f"Modularidade (comunidades): {metrics.modularity:.4f}")

    def top(metric_map, title):
        ranked = sorted(metric_map.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
        print(f"\nTop {top_n} — {title}:")
        for vid, score in ranked:
            print(f"  {idx_to_user[vid]:20s} {score:.6f}")

    top(metrics.degree_centrality, "Degree centrality")
    top(metrics.betweenness_centrality, "Betweenness centrality")
    top(metrics.closeness_centrality, "Closeness centrality")
    top(metrics.pagerank, "PageRank")
    top(metrics.eigenvector_centrality, "Eigenvector centrality")

    if metrics.bridging_ties:
        print("\nBridging ties (alta betweenness entre comunidades):")
        for vid in metrics.bridging_ties:
            print(f"  {idx_to_user[vid]}")


def _export_graphs(graph_set: GraphSet, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_set.comments_graph.exportToGEPHI(str(out_dir / "grafo1_comentarios.graphml"))
    graph_set.closes_graph.exportToGEPHI(str(out_dir / "grafo2_fechamentos.graphml"))
    graph_set.pr_actions_graph.exportToGEPHI(str(out_dir / "grafo3_pr_acoes.graphml"))
    graph_set.integrated_graph.exportToGEPHI(str(out_dir / "grafo_integrado.graphml"))


def _save_metrics(metrics, graph_set: GraphSet, path: Path) -> None:
    idx_to_user = {i: u for u, i in graph_set.user_index.items()}

    def map_users(d):
        return {idx_to_user[k]: v for k, v in d.items()}

    payload = {
        "density": metrics.density,
        "clustering_coefficient": metrics.clustering_coefficient,
        "assortativity": metrics.assortativity,
        "modularity": metrics.modularity,
        "degree_centrality": map_users(metrics.degree_centrality),
        "betweenness_centrality": map_users(metrics.betweenness_centrality),
        "closeness_centrality": map_users(metrics.closeness_centrality),
        "pagerank": map_users(metrics.pagerank),
        "eigenvector_centrality": map_users(metrics.eigenvector_centrality),
        "communities": {idx_to_user[k]: v for k, v in metrics.communities.items()},
        "bridging_ties": [idx_to_user[v] for v in metrics.bridging_ties],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _parse_env_file(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}

    env: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        env[key] = value
    return env


def load_env(env_path: Path = Path(".env")) -> None:
    for key, value in _parse_env_file(env_path).items():
        if key and value is not None:
            os.environ.setdefault(key, value)


def load_or_mine_interactions(
    repo: str,
    offline: bool,
    sample_path: Path,
    output_dir: Path,
    max_issues: int,
    max_pulls: int,
    use_cache: bool,
    workers: int,
) -> list:
    extractor = InteractionExtractor(workers=workers)
    cache = output_dir / "interactions_cache.json"

    if offline:
        interactions = extractor.load_interactions_json(sample_path)
        print(f"Modo offline: {len(interactions)} interações carregadas de {sample_path}")
    elif use_cache:
        cached = extractor.load_cache_if_valid(cache, repo, max_issues, max_pulls)
        if cached is not None:
            interactions = cached
            print(
                f"Cache válido: {len(interactions)} interações carregadas de {cache} "
                f"(use --no-cache para forçar nova mineração)"
            )
        else:
            print(f"Cache ausente ou incompatível em {cache}; minerando via GitHub API...")
            interactions = extractor.extract_from_repo(repo, max_issues=max_issues, max_pulls=max_pulls)
            output_dir.mkdir(parents=True, exist_ok=True)
            extractor.save_interactions_json(cache, interactions)
            extractor.save_cache_meta(cache, repo, max_issues, max_pulls, len(interactions))
            print(f"{len(interactions)} interações extraídas (cache salvo em {cache})")
    else:
        print(f"Minerando repositório {repo} via GitHub API ({workers} workers)...")
        interactions = extractor.extract_from_repo(repo, max_issues=max_issues, max_pulls=max_pulls)
        output_dir.mkdir(parents=True, exist_ok=True)
        extractor.save_interactions_json(cache, interactions)
        extractor.save_cache_meta(cache, repo, max_issues, max_pulls, len(interactions))
        print(f"{len(interactions)} interações extraídas (cache salvo em {cache})")

    if not interactions:
        raise RuntimeError("Nenhuma interação encontrada. Use --offline ou aumente limites/token GITHUB_TOKEN.")

    return interactions


def run_pipeline(
    repo: str,
    offline: bool,
    sample_path: Path,
    output_dir: Path,
    max_issues: int,
    max_pulls: int,
    use_cache: bool,
    workers: int,
) -> GraphSet:
    interactions = load_or_mine_interactions(
        repo, offline, sample_path, output_dir, max_issues, max_pulls, use_cache, workers
    )

    print("Construindo grafos a partir das interações...")
    graph_set = build_graphs_from_interactions(interactions)
    g = graph_set.integrated_graph
    print(
        f"  {len(graph_set.users)} usuários | "
        f"comentários: {graph_set.comments_graph.getEdgeCount()} arestas | "
        f"integrado: {g.getEdgeCount()} arestas"
    )

    print("Exportando arquivos GraphML...")
    _export_graphs(graph_set, output_dir)
    print("  4 arquivos .graphml salvos em", output_dir.resolve())

    print("Calculando métricas de rede (grafo integrado)...")
    metrics = compute_metrics(g, verbose=True)
    _save_metrics(metrics, graph_set, output_dir / "metricas_integrado.json")
    _print_top_users(graph_set, metrics)

    print(f"\nArquivos gerados em: {output_dir.resolve()}")
    return graph_set


def interactive_menu(args) -> None:
    interactions = None
    graph_set = None
    
    out_dir = Path(args.output)
    use_cache = args.use_cache and not args.no_cache
    
    while True:
        print("\n" + "=" * 50)
        print("                MENU PRINCIPAL")
        print("=" * 50)
        print("1 - Extrair / Carregar Dados (Mineração)")
        print("2 - Gerar todos os grafos")
        print("3 - Exportar grafo de comentários (.graphml)")
        print("4 - Exportar grafo de fechamentos (.graphml)")
        print("5 - Exportar grafo de ações de PR (.graphml)")
        print("6 - Exportar grafo integrado (.graphml)")
        print("7 - Analisar centralidade e métricas")
        print("8 - Executar Pipeline Completo (Automático)")
        print("0 - Sair")
        print("=" * 50)
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "0":
            print("Encerrando...")
            break
            
        elif opcao == "1":
            try:
                interactions = load_or_mine_interactions(
                    repo=args.repo,
                    offline=args.offline,
                    sample_path=Path(args.sample),
                    output_dir=out_dir,
                    max_issues=args.max_issues,
                    max_pulls=args.max_pulls,
                    use_cache=use_cache,
                    workers=args.workers,
                )
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
                
        elif opcao == "2":
            if not interactions:
                print("Por favor, execute a opção 1 primeiro para extrair/carregar os dados.")
                continue
            print("Construindo grafos a partir das interações...")
            graph_set = build_graphs_from_interactions(interactions)
            g = graph_set.integrated_graph
            print(
                f"  {len(graph_set.users)} usuários | "
                f"comentários: {graph_set.comments_graph.getEdgeCount()} arestas | "
                f"integrado: {g.getEdgeCount()} arestas"
            )
            print("Grafos gerados com sucesso!")
            
        elif opcao in ["3", "4", "5", "6"]:
            if not graph_set:
                print("Por favor, execute a opção 2 primeiro para gerar os grafos.")
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            if opcao == "3":
                path = out_dir / "grafo1_comentarios.graphml"
                graph_set.comments_graph.exportToGEPHI(str(path))
                print(f"Grafo exportado para {path}")
            elif opcao == "4":
                path = out_dir / "grafo2_fechamentos.graphml"
                graph_set.closes_graph.exportToGEPHI(str(path))
                print(f"Grafo exportado para {path}")
            elif opcao == "5":
                path = out_dir / "grafo3_pr_acoes.graphml"
                graph_set.pr_actions_graph.exportToGEPHI(str(path))
                print(f"Grafo exportado para {path}")
            elif opcao == "6":
                path = out_dir / "grafo_integrado.graphml"
                graph_set.integrated_graph.exportToGEPHI(str(path))
                print(f"Grafo exportado para {path}")
                
        elif opcao == "7":
            if not graph_set:
                print("Por favor, execute a opção 2 primeiro para gerar os grafos.")
                continue
            print("Calculando métricas de rede (grafo integrado)...")
            g = graph_set.integrated_graph
            metrics = compute_metrics(g, verbose=True)
            _save_metrics(metrics, graph_set, out_dir / "metricas_integrado.json")
            _print_top_users(graph_set, metrics)
            print(f"Métricas salvas em {out_dir / 'metricas_integrado.json'}")
            
        elif opcao == "8":
            try:
                graph_set = run_pipeline(
                    repo=args.repo,
                    offline=args.offline,
                    sample_path=Path(args.sample),
                    output_dir=out_dir,
                    max_issues=args.max_issues,
                    max_pulls=args.max_pulls,
                    use_cache=use_cache,
                    workers=args.workers,
                )
                print("Pipeline concluído com sucesso!")
            except Exception as e:
                print(f"Erro na execução do pipeline: {e}")
                
        else:
            print("Opção inválida.")


def main() -> None:
    load_env(Path(".env"))

    env_offline = os.environ.get("OFFLINE", "false").lower() in ("1", "true", "yes", "y")
    env_use_cache = os.environ.get("USE_CACHE", "false").lower() in ("1", "true", "yes", "y")
    parser = argparse.ArgumentParser(
        description="Ferramenta de análise de colaboração GitHub — fastapi/typer (Etapas 1–3)"
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("REPO", DEFAULT_REPO),
        help="owner/name ou URL do repositório",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=env_offline,
        help="usa dados de exemplo (sem chamar a API)",
    )
    parser.add_argument(
        "--sample",
        default=os.environ.get("SAMPLE", "data/sample_typer_interactions.json"),
        help="JSON de interações para modo offline",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("OUTPUT", "output"),
        help="pasta de saída",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=int(os.environ.get("MAX_ISSUES", "30")),
        help="limite de issues mineradas",
    )
    parser.add_argument(
        "--max-pulls",
        type=int,
        default=int(os.environ.get("MAX_PULLS", "30")),
        help="limite de PRs minerados",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.environ.get("WORKERS", "8")),
        help="requisições paralelas à API do GitHub",
    )
    cache_group = parser.add_mutually_exclusive_group()
    cache_group.add_argument(
        "--use-cache",
        action="store_true",
        default=env_use_cache,
        help="reutiliza interactions_cache.json se compatível com repo/limites",
    )
    cache_group.add_argument(
        "--no-cache",
        action="store_true",
        help="força nova mineração mesmo com --use-cache no .env",
    )
    args = parser.parse_args()

    interactive_menu(args)


if __name__ == "__main__":
    main()
