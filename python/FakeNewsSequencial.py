"""Execucao sequencial da simulacao de fake news."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from FakeNewsGraficos import gerar_grafico_historico
from FakeNewsModelo import (
    BOT,
    ESPALHADOR,
    FACT_CHECKER,
    IGNORANTE,
    INATIVO,
    INFLUENCIADOR,
    calcular_metricas,
    contar_estados,
    copiar_contexto,
    criar_contexto,
    imprimir_grade,
    proxima_geracao_sequencial,
    registrar_estatisticas,
)


def _imprimir_resumo_extra(contagem):
    print(
        f"Influenciadores: {contagem[INFLUENCIADOR]:,} | "
        f"Bots: {contagem[BOT]:,} | "
        f"Fact-checkers: {contagem[FACT_CHECKER]:,}"
    )


def executar_simulacao(
    linhas=500,
    colunas=500,
    geracoes=50,
    percentual_espalhadores=0.02,
    limiar_convencimento=2,
    semente=42,
    mostrar_grade=False,
    chance_convencimento=1.0,
    percentual_influenciadores=0.0,
    peso_influenciador=2,
    vida_influenciador=3,
    percentual_bots=0.0,
    percentual_fact_checkers=0.0,
    peso_fact_checker=2,
    gerar_grafico=False,
    caminho_grafico=None,
    mostrar_progresso=True,
):
    """Executa a simulacao sequencial usando o modelo compartilhado."""

    contexto = criar_contexto(
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
    contexto = copiar_contexto(contexto)
    grade = contexto["grade"]
    total_celulas = len(grade) * len(grade[0])
    historico = []

    contagem_inicial = registrar_estatisticas(historico, grade, 0)
    if mostrar_progresso:
        print("=== SIMULACAO SEQUENCIAL DE PROPAGACAO DE FAKE NEWS ===")
        print(f"Tamanho da grade: {linhas} x {colunas} ({total_celulas:,} pessoas)")
        print(f"Geracoes: {geracoes}")
        print(
            "Percentual inicial de espalhadores: "
            f"{contagem_inicial[ESPALHADOR] / total_celulas * 100:.2f}% "
            f"({contagem_inicial[ESPALHADOR]:,} espalhadores reais)"
        )
        print(f"Limiar de convencimento: {limiar_convencimento} vizinhos")
        print(f"Chance de convencimento: {chance_convencimento:.2f}")
        _imprimir_resumo_extra(contagem_inicial)
        print()

    inicio = time.perf_counter()
    geracao_executada = 0

    for geracao in range(geracoes):
        contexto = proxima_geracao_sequencial(contexto, limiar_convencimento, geracao + 1)
        geracao_executada = geracao + 1
        grade = contexto["grade"]

        contagem = registrar_estatisticas(historico, grade, geracao_executada)
        if mostrar_progresso:
            print(
                f"Geracao {geracao_executada:03d} | "
                f"Ignorantes: {contagem[IGNORANTE]:>10,} | "
                f"Espalhadores: {contagem[ESPALHADOR]:>10,} | "
                f"Inativos: {contagem[INATIVO]:>10,}"
            )

        if mostrar_grade:
            imprimir_grade(grade)

        if contagem["propagadores_variaveis"] == 0:
            if mostrar_progresso:
                print("\nA propagacao terminou: nao ha mais espalhadores variaveis.")
            break

    tempo_total = time.perf_counter() - inicio
    contagem_final = contar_estados(grade)
    metricas = calcular_metricas(historico, tempo_total, geracao_executada)

    if mostrar_progresso:
        print()
        print("=== RESULTADO FINAL ===")
        print(f"Tempo total de execucao: {tempo_total:.4f} segundos")
        print(
            f"Ignorantes finais: {contagem_final[IGNORANTE]:,} "
            f"({contagem_final[IGNORANTE] / total_celulas * 100:.2f}%)"
        )
        print(
            f"Espalhadores finais: {contagem_final[ESPALHADOR]:,} "
            f"({contagem_final[ESPALHADOR] / total_celulas * 100:.2f}%)"
        )
        print(
            f"Inativos finais: {contagem_final[INATIVO]:,} "
            f"({contagem_final[INATIVO] / total_celulas * 100:.2f}%)"
        )
        _imprimir_resumo_extra(contagem_final)
        print(
            f"Pico de espalhamento: {metricas['pico_espalhamento']} "
            f"(geracao {metricas['geracao_pico']})"
        )
        print(f"Geracao de estabilizacao: {metricas['geracao_estabilizacao']}")

    if gerar_grafico:
        caminho = caminho_grafico or Path("graficos") / "fake_news_sequencial.png"
        caminho_real = gerar_grafico_historico(historico, caminho)
        print(f"Grafico gerado em: {caminho_real}")

    return {
        "contexto_final": contexto,
        "grade_final": grade,
        "tempo": tempo_total,
        "geracoes_executadas": geracao_executada,
        "contagem_final": contagem_final,
        "historico": historico,
        "metricas": metricas,
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Fake news simulation - sequential mode")
    parser.add_argument("--linhas", type=int, default=500)
    parser.add_argument("--colunas", type=int, default=500)
    parser.add_argument("--geracoes", type=int, default=50)
    parser.add_argument("--percentual", type=float, default=0.02)
    parser.add_argument("--limiar", type=int, default=2)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--mostrar-grade", action="store_true")
    parser.add_argument("--chance-convencimento", type=float, default=1.0)
    parser.add_argument("--percentual-influenciadores", type=float, default=0.0)
    parser.add_argument("--peso-influenciador", type=int, default=2)
    parser.add_argument("--vida-influenciador", type=int, default=3)
    parser.add_argument("--percentual-bots", type=float, default=0.0)
    parser.add_argument("--percentual-fact-checkers", type=float, default=0.0)
    parser.add_argument("--peso-fact-checker", type=int, default=2)
    parser.add_argument("--gerar-grafico", action="store_true")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    executar_simulacao(
        linhas=args.linhas,
        colunas=args.colunas,
        geracoes=args.geracoes,
        percentual_espalhadores=args.percentual,
        limiar_convencimento=args.limiar,
        semente=args.semente,
        mostrar_grade=args.mostrar_grade,
        chance_convencimento=args.chance_convencimento,
        percentual_influenciadores=args.percentual_influenciadores,
        peso_influenciador=args.peso_influenciador,
        vida_influenciador=args.vida_influenciador,
        percentual_bots=args.percentual_bots,
        percentual_fact_checkers=args.percentual_fact_checkers,
        peso_fact_checker=args.peso_fact_checker,
        gerar_grafico=args.gerar_grafico,
    )


if __name__ == "__main__":
    main()
