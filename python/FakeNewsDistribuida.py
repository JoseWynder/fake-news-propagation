"""Execucao distribuida da simulacao de fake news usando sockets."""

from __future__ import annotations

import argparse
import json
import socket
import time
from threading import Thread

from FakeNewsModelo import (
    ESPALHADOR,
    IGNORANTE,
    INATIVO,
    copiar_grade,
    contar_estados,
    dividir_faixas,
    imprimir_grade,
    criar_grade,
    construir_bloco_com_halos,
)


def _packed_send(conexao, payload):
    # Envia tamanho + JSON para evitar problemas com mensagens truncadas.
    dados = json.dumps(payload).encode("utf-8")
    conexao.sendall(len(dados).to_bytes(8, byteorder="big"))
    conexao.sendall(dados)


def _packed_recv(conexao):
    # Primeiro lemos o tamanho e depois o corpo completo da mensagem.
    tamanho_bytes = _recv_exact(conexao, 8)
    tamanho = int.from_bytes(tamanho_bytes, byteorder="big")
    dados = _recv_exact(conexao, tamanho)
    return json.loads(dados.decode("utf-8"))


def _recv_exact(conexao, tamanho):
    buffer = bytearray()
    while len(buffer) < tamanho:
        bloco = conexao.recv(tamanho - len(buffer))
        if not bloco:
            raise ConnectionError("Socket closed while receiving data.")
        buffer.extend(bloco)
    return bytes(buffer)


def _trabalhador_socket(endereco, tarefa, limiar_convencimento, resultados, indice_resultado):
    host, porta = endereco
    inicio, fim, bloco = tarefa

    try:
        # Cada thread cliente conversa com um worker distinto.
        with socket.create_connection((host, porta), timeout=15) as conexao:
            _packed_send(
                conexao,
                {
                    "acao": "calcular_faixa",
                    "inicio": inicio,
                    "fim": fim,
                    "limiar_convencimento": limiar_convencimento,
                    "bloco": bloco,
                },
            )
            resposta = _packed_recv(conexao)

        if "erro" in resposta:
            raise RuntimeError(resposta["erro"])

        resultados[indice_resultado] = (resposta["inicio"], resposta["linhas"])
    except Exception as exc:
        resultados[indice_resultado] = exc


def proxima_geracao_distribuida(grade, limiar_convencimento, workers):
    faixas = dividir_faixas(len(grade), len(workers))
    if not faixas:
        return []

    tarefas = []
    # Cada worker recebe o bloco com as fronteiras extras para calcular moore
    for (inicio, fim), endereco in zip(faixas, workers):
        bloco = construir_bloco_com_halos(grade, inicio, fim)
        tarefas.append((endereco, (inicio, fim, bloco)))

    resultados = [None] * len(tarefas)
    threads = []

    for indice, (endereco, tarefa) in enumerate(tarefas):
        thread = Thread(
            target=_trabalhador_socket,
            args=(endereco, tarefa, limiar_convencimento, resultados, indice),
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        # Espera todas as respostas antes de montar a nova geracao global.
        thread.join()

    nova_grade = []
    for item in sorted(resultados, key=lambda valor: valor[0] if isinstance(valor, tuple) else -1):
        if isinstance(item, Exception):
            raise item
        nova_grade.extend(item[1])

    return nova_grade


def _parse_workers(raw_workers):
    workers = []
    for entrada in raw_workers:
        for item in entrada.split(","):
            item = item.strip()
            if not item:
                continue
            host, porta = item.rsplit(":", 1)
            workers.append((host, int(porta)))
    return workers


def executar_distribuida(
    grade_inicial,
    geracoes,
    limiar_convencimento,
    workers,
    mostrar_grade=False,
    mostrar_progresso=True,
):
    grade = copiar_grade(grade_inicial)
    total_celulas = len(grade) * len(grade[0])

    if mostrar_progresso:
        contagem_inicial = contar_estados(grade)
        print("=== SIMULACAO DISTRIBUIDA DE PROPAGACAO DE FAKE NEWS ===")
        print(f"Tamanho da grade: {len(grade)} x {len(grade[0])} ({total_celulas:,} pessoas)")
        print(f"Geracoes: {geracoes}")
        print(
            "Percentual inicial de espalhadores: "
            f"{contagem_inicial[ESPALHADOR] / total_celulas * 100:.2f}% "
            f"({contagem_inicial[ESPALHADOR]:,} espalhadores reais)"
        )
        print(f"Limiar de convencimento: {limiar_convencimento} vizinhos")
        print(f"Workers: {len(workers)}")
        print()

    inicio_tempo = time.perf_counter()

    geracao_executada = 0
    for geracao in range(geracoes):
        # O mestre coordena uma geracao inteira por vez.
        grade = proxima_geracao_distribuida(grade, limiar_convencimento, workers)
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
    parser = argparse.ArgumentParser(description="Fake news simulation - distributed mode")
    parser.add_argument("--linhas", type=int, default=500)
    parser.add_argument("--colunas", type=int, default=500)
    parser.add_argument("--geracoes", type=int, default=50)
    parser.add_argument("--percentual", type=float, default=0.02)
    parser.add_argument("--limiar", type=int, default=2)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--workers", nargs="+", required=True, help="Lista de host:port")
    parser.add_argument("--mostrar-grade", action="store_true")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    workers = _parse_workers(args.workers)
    grade_inicial = criar_grade(
        args.linhas,
        args.colunas,
        percentual_espalhadores=args.percentual,
        semente=args.semente,
    )

    executar_distribuida(
        grade_inicial,
        args.geracoes,
        args.limiar,
        workers,
        mostrar_grade=args.mostrar_grade,
        mostrar_progresso=True,
    )


if __name__ == "__main__":
    main()
