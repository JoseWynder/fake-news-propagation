"""Geracao opcional de graficos do historico da simulacao."""

from __future__ import annotations

from pathlib import Path


def gerar_grafico_historico(historico, caminho_saida):
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Matplotlib nao esta instalado. Rode sem --gerar-grafico ou instale a biblioteca."
        ) from exc

    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    geracoes = [item["geracao"] for item in historico]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(geracoes, [item["ignorantes"] for item in historico], label="Ignorantes", linewidth=2)
    ax.plot(geracoes, [item["propagadores_totais"] for item in historico], label="Propagadores", linewidth=2)
    ax.plot(geracoes, [item["inativos"] for item in historico], label="Inativos", linewidth=2)

    if any(item["influenciadores"] for item in historico):
        ax.plot(geracoes, [item["influenciadores"] for item in historico], label="Influenciadores", linewidth=2)
    if any(item["bots"] for item in historico):
        ax.plot(geracoes, [item["bots"] for item in historico], label="Bots", linewidth=2)
    if any(item["fact_checkers"] for item in historico):
        ax.plot(geracoes, [item["fact_checkers"] for item in historico], label="Fact-checkers", linewidth=2)

    ax.set_title("Curva de propagacao da fake news")
    ax.set_xlabel("Geracao")
    ax.set_ylabel("Quantidade de individuos")
    ax.legend()
    fig.tight_layout()
    fig.savefig(caminho_saida, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return caminho_saida
