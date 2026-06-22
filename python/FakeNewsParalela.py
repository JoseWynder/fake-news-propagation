"""Execucao paralela da simulacao de fake news usando threads."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from threading import Thread

from FakeNewsGraficos import gerar_grafico_historico
from FakeNewsModelo import (
    BOT,
    ESPALHADOR,
    FACT_CHECKER,
    IGNORANTE,
    INATIVO,
    INFLUENCIADOR,
    calcular_linha_proxima_geracao,
    calcular_metricas,
    contar_estados,
    copiar_contexto,
    criar_contexto,
    dividir_faixas,
    imprimir_grade,
    registrar_estatisticas,
)


def _trabalhador_faixa(contexto, inicio, fim, limiar_convencimento, geracao, resultados, indice_resultado):
    try:
        linhas = []
        duracoes = []
        for i in range(inicio, fim):
            linha, duracao = calcular_linha_proxima_geracao(
                contexto["grade"],
                contexto["duracoes"],
                i,
                limiar_convencimento,
                geracao,
                contexto["config"],
            )
            linhas.append(linha)
            duracoes.append(duracao)

        resultados[indice_resultado] = (inicio, linhas, duracoes)
    except Exception as exc:
        resultados[indice_resultado] = exc


def proxima_geracao_paralela(contexto, limiar_convencimento=2, quantidade_threads=4, geracao=1):
    faixas = dividir_faixas(len(contexto["grade"]), quantidade_threads)
    if not faixas:
        return copiar_contexto(contexto)

    resultados = [None] * len(faixas)
    threads = []

    for indice, (inicio, fim) in enumerate(faixas):
        thread = Thread(
            target=_trabalhador_faixa,
            args=(contexto, inicio, fim, limiar_convencimento, geracao, resultados, indice),
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    nova_grade = []
    nova_duracao = []
    for item in sorted(resultados, key=lambda valor: valor[0] if isinstance(valor, tuple) else -1):
        if isinstance(item, Exception):
            raise item
        nova_grade.extend(item[1])
        nova_duracao.extend(item[2])

    return {
        "grade": nova_grade,
        "duracoes": nova_duracao,
        "config": dict(contexto["config"]),
    }


def _imprimir_resumo_extra(contagem):
    print(
        f"Influenciadores: {contagem[INFLUENCIADOR]:,} | "
        f"Bots: {contagem[BOT]:,} | "
        f"Fact-checkers: {contagem[FACT_CHECKER]:,}"
    )


def executar_paralela(
    contexto_inicial,
    geracoes,
    limiar_convencimento,
    quantidade_threads,
    mostrar_grade=False,
    mostrar_progresso=True,
    gerar_grafico=False,
    caminho_grafico=None,
):
    contexto = copiar_contexto(contexto_inicial)
    grade = contexto["grade"]
    total_celulas = len(grade) * len(grade[0])
    historico = []

    if mostrar_progresso:
        contagem_inicial = registrar_estatisticas(historico, grade, 0)
        print("=== SIMULACAO PARALELA DE PROPAGACAO DE FAKE NEWS ===")
        print(f"Tamanho da grade: {len(grade)} x {len(grade[0])} ({total_celulas:,} pessoas)")
        print(f"Geracoes: {geracoes}")
        print(
            "Percentual inicial de espalhadores: "
            f"{contagem_inicial[ESPALHADOR] / total_celulas * 100:.2f}% "
            f"({contagem_inicial[ESPALHADOR]:,} espalhadores reais)"
        )
        print(f"Limiar de convencimento: {limiar_convencimento} vizinhos")
        print(f"Threads: {quantidade_threads}")
        _imprimir_resumo_extra(contagem_inicial)
        print()
    else:
        registrar_estatisticas(historico, grade, 0)

    inicio_tempo = time.perf_counter()
    geracao_executada = 0

    for geracao in range(geracoes):
        contexto = proxima_geracao_paralela(contexto, limiar_convencimento, quantidade_threads, geracao + 1)
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

    tempo_total = time.perf_counter() - inicio_tempo
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
        caminho = caminho_grafico or Path("graficos") / "fake_news_paralela.png"
        gerar_grafico_historico(historico, caminho)

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
    parser = argparse.ArgumentParser(description="Fake news simulation - parallel mode")
    parser.add_argument("--linhas", type=int, default=500)
    parser.add_argument("--colunas", type=int, default=500)
    parser.add_argument("--geracoes", type=int, default=50)
    parser.add_argument("--percentual", type=float, default=0.02)
    parser.add_argument("--limiar", type=int, default=2)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--threads", type=int, default=4)
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

    contexto_inicial = criar_contexto(
        args.linhas,
        args.colunas,
        percentual_espalhadores=args.percentual,
        percentual_influenciadores=args.percentual_influenciadores,
        percentual_bots=args.percentual_bots,
        percentual_fact_checkers=args.percentual_fact_checkers,
        semente=args.semente,
        chance_convencimento=args.chance_convencimento,
        peso_influenciador=args.peso_influenciador,
        vida_influenciador=args.vida_influenciador,
        peso_fact_checker=args.peso_fact_checker,
    )

    executar_paralela(
        contexto_inicial,
        args.geracoes,
        args.limiar,
        args.threads,
        mostrar_grade=args.mostrar_grade,
        mostrar_progresso=True,
        gerar_grafico=args.gerar_grafico,
    )


if __name__ == "__main__":
    main()
