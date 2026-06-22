"""Worker da simulacao distribuida de fake news"""

from __future__ import annotations

import argparse
import json
import socket

from FakeNewsModelo import processar_bloco_distribuido


def _packed_send(conexao, payload):
    dados = json.dumps(payload).encode("utf-8")
    conexao.sendall(len(dados).to_bytes(8, byteorder="big"))
    conexao.sendall(dados)


def _packed_recv(conexao):
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


def worker_main(host, port):
    print(f"Worker ativo em {host}:{port}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((host, port))
        servidor.listen()

        while True:
            conexao, endereco = servidor.accept()
            with conexao:
                try:
                    pedido = _packed_recv(conexao)

                    if pedido.get("acao") == "encerrar":
                        _packed_send(conexao, {"status": "ok"})
                        print(f"Worker encerrado em {endereco}")
                        return

                    if pedido.get("acao") != "calcular_faixa":
                        raise ValueError("Acao invalida.")

                    linhas = processar_bloco_distribuido(
                        pedido["bloco"],
                        pedido["limiar_convencimento"],
                    )
                    _packed_send(
                        conexao,
                        {
                            "inicio": pedido["inicio"],
                            "fim": pedido["fim"],
                            "linhas": linhas,
                        },
                    )
                except Exception as exc:
                    try:
                        _packed_send(conexao, {"erro": str(exc)})
                    except Exception:
                        pass


def build_parser():
    parser = argparse.ArgumentParser(description="Fake news worker")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, required=True)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    worker_main(args.host, args.port)


if __name__ == "__main__":
    main()
