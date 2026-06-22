"""Benchmark das versoes sequencial, paralela e distribuida."""

from __future__ import annotations

import argparse

from FakeNewsDistribuida import _parse_workers, executar_distribuida
from FakeNewsModelo import copiar_contexto, criar_contexto
from FakeNewsParalela import executar_paralela
from FakeNewsSequencial import executar_simulacao


def executar_benchmark(
    linhas,
    colunas,
    geracoes,
    percentual_espalhadores,
    limiar_convencimento,
    quantidade_threads,
    workers,
    semente=42,
    chance_convencimento=1.0,
    percentual_influenciadores=0.0,
    peso_influenciador=2,
    vida_influenciador=3,
    percentual_bots=0.0,
    percentual_fact_checkers=0.0,
    peso_fact_checker=2,
):
    contexto_inicial = criar_contexto(
        linhas=linhas,
        colunas=colunas,
        percentual_espalhadores=percentual_espalhadores,
        percentual_influenciadores=percentual_influenciadores,
        percentual_bots=percentual_bots,
        percentual_fact_checkers=percentual_fact_checkers,
        semente=semente,
        chance_convencimento=chance_convencimento,
        peso_influenciador=peso_influenciador,
        vida_influenciador=vida_influenciador,
        peso_fact_checker=peso_fact_checker,
    )

    resultados = {}
    resultados["sequencial"] = executar_simulacao(
        linhas=linhas,
        colunas=colunas,
        geracoes=geracoes,
        percentual_espalhadores=percentual_espalhadores,
        limiar_convencimento=limiar_convencimento,
        semente=semente,
        chance_convencimento=chance_convencimento,
        percentual_influenciadores=percentual_influenciadores,
        peso_influenciador=peso_influenciador,
        vida_influenciador=vida_influenciador,
        percentual_bots=percentual_bots,
        percentual_fact_checkers=percentual_fact_checkers,
        peso_fact_checker=peso_fact_checker,
        mostrar_grade=False,
        gerar_grafico=False,
        mostrar_progresso=False,
    )
    resultados["paralela"] = executar_paralela(
        copiar_contexto(contexto_inicial),
        geracoes,
        limiar_convencimento,
        quantidade_threads,
        mostrar_grade=False,
        mostrar_progresso=False,
        gerar_grafico=False,
    )
    resultados["distribuida"] = executar_distribuida(
        copiar_contexto(contexto_inicial),
        geracoes,
        limiar_convencimento,
        workers,
        mostrar_grade=False,
        mostrar_progresso=False,
        gerar_grafico=False,
    )

    tempo_base = resultados["sequencial"]["tempo"]
    total_workers_distribuidos = max(1, len(workers))

    print("=== COMPARACAO DE DESEMPENHO ===")
    print(f"Sequencial : {tempo_base:.4f} s")

    tempo_paralela = resultados["paralela"]["tempo"]
    tempo_distribuida = resultados["distribuida"]["tempo"]

    print(
        f"Paralela   : {tempo_paralela:.4f} s | "
        f"speedup = {tempo_base / tempo_paralela:.2f} | "
        f"eficiencia = {(tempo_base / tempo_paralela) / quantidade_threads:.2f}"
    )
    print(
        f"Distribuida: {tempo_distribuida:.4f} s | "
        f"speedup = {tempo_base / tempo_distribuida:.2f} | "
        f"eficiencia = {(tempo_base / tempo_distribuida) / total_workers_distribuidos:.2f}"
    )

    if resultados["sequencial"]["grade_final"] != resultados["paralela"]["grade_final"]:
        print("Aviso: a versao paralela nao bateu com a sequencial.")
    if resultados["sequencial"]["grade_final"] != resultados["distribuida"]["grade_final"]:
        print("Aviso: a versao distribuida nao bateu com a sequencial.")


def build_parser():
    parser = argparse.ArgumentParser(description="Fake news benchmark")
    parser.add_argument("--linhas", type=int, default=500)
    parser.add_argument("--colunas", type=int, default=500)
    parser.add_argument("--geracoes", type=int, default=50)
    parser.add_argument("--percentual", type=float, default=0.02)
    parser.add_argument("--limiar", type=int, default=2)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--workers", nargs="+", required=True, help="Lista de host:port")
    parser.add_argument("--chance-convencimento", type=float, default=1.0)
    parser.add_argument("--percentual-influenciadores", type=float, default=0.0)
    parser.add_argument("--peso-influenciador", type=int, default=2)
    parser.add_argument("--vida-influenciador", type=int, default=3)
    parser.add_argument("--percentual-bots", type=float, default=0.0)
    parser.add_argument("--percentual-fact-checkers", type=float, default=0.0)
    parser.add_argument("--peso-fact-checker", type=int, default=2)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    workers = _parse_workers(args.workers)

    executar_benchmark(
        args.linhas,
        args.colunas,
        args.geracoes,
        args.percentual,
        args.limiar,
        args.threads,
        workers,
        semente=args.semente,
        chance_convencimento=args.chance_convencimento,
        percentual_influenciadores=args.percentual_influenciadores,
        peso_influenciador=args.peso_influenciador,
        vida_influenciador=args.vida_influenciador,
        percentual_bots=args.percentual_bots,
        percentual_fact_checkers=args.percentual_fact_checkers,
        peso_fact_checker=args.peso_fact_checker,
    )


if __name__ == "__main__":
    main()
