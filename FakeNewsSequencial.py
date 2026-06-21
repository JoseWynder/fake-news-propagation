"""Execucao paralela da simulacao de fake news usando threads."""

from __future__ import annotations

import argparse
import time
from threading import Thread

from FakeNewsModelo import (
    ESPALHADOR,
    IGNORANTE,
    INATIVO,
    copiar_grade,
    contar_estados,
    calcular_linha_proxima_geracao,
    criar_grade,
    dividir_faixas,
    imprimir_grade,
)


def _trabalhador_faixa(grade, inicio, fim, limiar_convencimento, resultados, indice_resultado):
    try:
        # Cada thread escreve apenas no seu espaco de resultado.
        resultados[indice_resultado] = (
            inicio,
            [calcular_linha_proxima_geracao(grade, i, limiar_convencimento) for i in range(inicio, fim)],
        )
    except Exception as exc:
        resultados[indice_resultado] = exc


def proxima_geracao_paralela(grade, limiar_convencimento=2, quantidade_threads=4):
    faixas = dividir_faixas(len(grade), quantidade_threads)
    if not faixas:
        return []

    resultados = [None] * len(faixas)
    threads = []

    # Divisao e estavel: uma faixa continua de linhas por thread
    for indice, (inicio, fim) in enumerate(faixas):
        thread = Thread(
            target=_trabalhador_faixa,
            args=(grade, inicio, fim, limiar_convencimento, resultados, indice),
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        # O join garante que a proxima geracao so avance quando todas terminarem
        thread.join()

    nova_grade = []
    for item in sorted(resultados, key=lambda valor: valor[0] if isinstance(valor, tuple) else -1):
        if isinstance(item, Exception):
            raise item
        nova_grade.extend(item[1])

    return nova_grade


def executar_paralela(
    grade_inicial,
    geracoes,
    limiar_convencimento,
    quantidade_threads,
    mostrar_grade=False,
    mostrar_progresso=True,
):
    grade = copiar_grade(grade_inicial)
    total_celulas = len(grade) * len(grade[0])

    if mostrar_progresso:
        contagem_inicial = contar_estados(grade)
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
        print()

    inicio_tempo = time.perf_counter()

    geracao_executada = 0
    for geracao in range(geracoes):
        grade = proxima_geracao_paralela(grade, limiar_convencimento, quantidade_threads)
        geracao_executada = geracao + 1

        contagem = contar_estados(grade)

        if mostrar_progresso:
            print(
                f"Geracao {geracao + 1:03d} | "
                f"Ignorantes: {contagem[IGNORANTE]:>10,} | "
                f"Espalhadores: {contagem[ESPALHADOR]:>10,} | "
                f"Inativos: {contagem[INATIVO]:>10,}"
            )

        if mostrar_grade:
            imprimir_grade(grade)

        if contagem[ESPALHADOR] == 0:
            if mostrar_progresso:
                print("\nA propagacao terminou: nao ha mais espalhadores.")
            break

    tempo_total = time.perf_counter() - inicio_tempo
    contagem_final = contar_estados(grade)

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

    return {
        "grade_final": grade,
        "tempo": tempo_total,
        "geracoes_executadas": geracao_executada,
        "contagem_final": contagem_final,
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
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    grade_inicial = criar_grade(
        args.linhas,
        args.colunas,
        percentual_espalhadores=args.percentual,
        semente=args.semente,
    )

    executar_paralela(
        grade_inicial,
        args.geracoes,
        args.limiar,
        args.threads,
        mostrar_grade=args.mostrar_grade,
        mostrar_progresso=True,
    )


if __name__ == "__main__":
    main()
