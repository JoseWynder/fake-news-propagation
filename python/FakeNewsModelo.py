"""Modelo compartilhado da simulacao de fake news.

Este modulo concentra a logica reutilizada pelas versoes sequencial,
paralela e distribuida, incluindo as melhorias opcionais do projeto.
"""

from __future__ import annotations

import random

IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2
INFLUENCIADOR = 3
BOT = 4
FACT_CHECKER = 5


def criar_configuracao(**kwargs):
    config = {
        "linhas": kwargs.get("linhas", 500),
        "colunas": kwargs.get("colunas", 500),
        "percentual_espalhadores": kwargs.get("percentual_espalhadores", 0.02),
        "percentual_influenciadores": kwargs.get("percentual_influenciadores", 0.0),
        "percentual_bots": kwargs.get("percentual_bots", 0.0),
        "percentual_fact_checkers": kwargs.get("percentual_fact_checkers", 0.0),
        "semente": kwargs.get("semente", 42),
        "chance_convencimento": kwargs.get("chance_convencimento", 1.0),
        "peso_influenciador": kwargs.get("peso_influenciador", 2),
        "vida_influenciador": kwargs.get("vida_influenciador", 3),
        "peso_fact_checker": kwargs.get("peso_fact_checker", 2),
    }
    return config


def copiar_grade(grade):
    # Cria uma copia rasa por linha para manter cada geracao isolada.
    return [linha[:] for linha in grade]


def copiar_contexto(contexto):
    return {
        "grade": copiar_grade(contexto["grade"]),
        "duracoes": copiar_grade(contexto["duracoes"]),
        "config": dict(contexto["config"]),
    }


def criar_contexto(
    linhas,
    colunas,
    percentual_espalhadores=0.02,
    percentual_influenciadores=0.0,
    percentual_bots=0.0,
    percentual_fact_checkers=0.0,
    semente=42,
    chance_convencimento=1.0,
    peso_influenciador=2,
    vida_influenciador=3,
    peso_fact_checker=2,
):
    config = criar_configuracao(
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

    grade, duracoes = criar_grade(config)
    return {
        "grade": grade,
        "duracoes": duracoes,
        "config": config,
    }


def criar_grade(config):
    """Cria uma grade deterministica com estados iniciais sem sobreposicao."""

    linhas = config["linhas"]
    colunas = config["colunas"]
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]
    duracoes = [[0 for _ in range(colunas)] for _ in range(linhas)]

    total_celulas = linhas * colunas
    rng = random.Random(config["semente"])

    alocacoes = [
        (ESPALHADOR, int(total_celulas * config["percentual_espalhadores"])),
        (INFLUENCIADOR, int(total_celulas * config["percentual_influenciadores"])),
        (BOT, int(total_celulas * config["percentual_bots"])),
        (FACT_CHECKER, int(total_celulas * config["percentual_fact_checkers"])),
    ]
    total_ocupado = sum(max(0, quantidade) for _, quantidade in alocacoes)
    total_ocupado = min(total_ocupado, total_celulas)

    if total_ocupado <= 0:
        return grade, duracoes

    posicoes = rng.sample(range(total_celulas), total_ocupado)
    cursor = 0

    for estado, quantidade in alocacoes:
        quantidade = max(0, min(quantidade, total_celulas - cursor))
        for posicao in posicoes[cursor : cursor + quantidade]:
            i, j = divmod(posicao, colunas)
            grade[i][j] = estado
            if estado == INFLUENCIADOR:
                duracoes[i][j] = config["vida_influenciador"]
        cursor += quantidade

    return grade, duracoes


def contar_vizinhos_ponderados(grade, i, j, config):
    """Soma a influencia ponderada na vizinhanca de Moore."""

    linhas = len(grade)
    colunas = len(grade[0])
    total = 0

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue

            ni = i + di
            nj = j + dj

            if 0 <= ni < linhas and 0 <= nj < colunas:
                estado = grade[ni][nj]
                if estado == ESPALHADOR:
                    total += 1
                elif estado == INFLUENCIADOR:
                    total += config["peso_influenciador"]
                elif estado == BOT:
                    total += 1
                elif estado == FACT_CHECKER:
                    total -= config["peso_fact_checker"]

    return total


def _chance_aprovada(config, geracao, i, j):
    chance = config["chance_convencimento"]
    if chance >= 1.0:
        return True
    if chance <= 0.0:
        return False

    mistura = (
        config["semente"] * 1_000_003
        + geracao * 9_176
        + i * 1_315_423_911
        + j * 2_654_435_761
    ) & 0xFFFFFFFFFFFF
    return random.Random(mistura).random() <= chance


def calcular_linha_proxima_geracao(grade, duracoes, i, limiar_convencimento, geracao, config):
    """Calcula uma linha da proxima geracao a partir do estado atual."""

    nova_linha = grade[i][:]
    nova_duracao = duracoes[i][:]

    for j in range(len(grade[0])):
        estado_atual = grade[i][j]

        if estado_atual == IGNORANTE:
            peso = contar_vizinhos_ponderados(grade, i, j, config)
            if peso >= limiar_convencimento and _chance_aprovada(config, geracao, i, j):
                nova_linha[j] = ESPALHADOR
                nova_duracao[j] = 0
            else:
                nova_linha[j] = IGNORANTE
                nova_duracao[j] = 0
        elif estado_atual == ESPALHADOR:
            nova_linha[j] = INATIVO
            nova_duracao[j] = 0
        elif estado_atual == INATIVO:
            nova_linha[j] = INATIVO
            nova_duracao[j] = 0
        elif estado_atual == INFLUENCIADOR:
            restante = duracoes[i][j] if duracoes[i][j] > 0 else config["vida_influenciador"]
            if restante > 1:
                nova_linha[j] = INFLUENCIADOR
                nova_duracao[j] = restante - 1
            else:
                nova_linha[j] = INATIVO
                nova_duracao[j] = 0
        elif estado_atual == BOT:
            nova_linha[j] = BOT
            nova_duracao[j] = 0
        elif estado_atual == FACT_CHECKER:
            nova_linha[j] = FACT_CHECKER
            nova_duracao[j] = 0

    return nova_linha, nova_duracao


def proxima_geracao_sequencial(contexto, limiar_convencimento=2, geracao=1):
    grade = contexto["grade"]
    duracoes = contexto["duracoes"]
    config = contexto["config"]

    nova_grade = []
    nova_duracao = []

    for i in range(len(grade)):
        linha, duracao = calcular_linha_proxima_geracao(
            grade,
            duracoes,
            i,
            limiar_convencimento,
            geracao,
            config,
        )
        nova_grade.append(linha)
        nova_duracao.append(duracao)

    return {
        "grade": nova_grade,
        "duracoes": nova_duracao,
        "config": dict(config),
    }


def dividir_faixas(total_linhas, quantidade_partes):
    # Divide o trabalho em blocos contiguos de linhas.
    if total_linhas <= 0:
        return []

    quantidade_partes = max(1, min(quantidade_partes, total_linhas))
    base = total_linhas // quantidade_partes
    resto = total_linhas % quantidade_partes

    faixas = []
    inicio = 0

    for indice in range(quantidade_partes):
        tamanho = base + (1 if indice < resto else 0)
        fim = inicio + tamanho
        if inicio < fim:
            faixas.append((inicio, fim))
        inicio = fim

    return faixas


def contar_estados(grade):
    contagem = {
        IGNORANTE: 0,
        ESPALHADOR: 0,
        INATIVO: 0,
        INFLUENCIADOR: 0,
        BOT: 0,
        FACT_CHECKER: 0,
        "propagadores_totais": 0,
        "propagadores_variaveis": 0,
    }

    for linha in grade:
        for celula in linha:
            contagem[celula] += 1

    contagem["propagadores_totais"] = contagem[ESPALHADOR] + contagem[INFLUENCIADOR] + contagem[BOT]
    contagem["propagadores_variaveis"] = contagem[ESPALHADOR] + contagem[INFLUENCIADOR]
    return contagem


def registrar_estatisticas(historico, grade, geracao):
    contagem = contar_estados(grade)
    historico.append(
        {
            "geracao": geracao,
            "ignorantes": contagem[IGNORANTE],
            "espalhadores": contagem[ESPALHADOR],
            "inativos": contagem[INATIVO],
            "influenciadores": contagem[INFLUENCIADOR],
            "bots": contagem[BOT],
            "fact_checkers": contagem[FACT_CHECKER],
            "propagadores_totais": contagem["propagadores_totais"],
            "propagadores_variaveis": contagem["propagadores_variaveis"],
        }
    )
    return contagem


def calcular_metricas(historico, tempo_total, geracoes_executadas):
    if not historico:
        return {
            "pico_espalhamento": 0,
            "geracao_pico": 0,
            "geracao_estabilizacao": None,
            "tempo_total": tempo_total,
            "geracoes_executadas": geracoes_executadas,
        }

    pico = max(historico, key=lambda item: item["propagadores_totais"])
    geracao_estabilizacao = None

    for item in historico:
        if item["geracao"] == 0:
            continue
        if item["propagadores_variaveis"] == 0:
            geracao_estabilizacao = item["geracao"]
            break

    return {
        "pico_espalhamento": pico["propagadores_totais"],
        "geracao_pico": pico["geracao"],
        "geracao_estabilizacao": geracao_estabilizacao,
        "tempo_total": tempo_total,
        "geracoes_executadas": geracoes_executadas,
    }


def imprimir_grade(grade, limite=30):
    simbolos = {
        IGNORANTE: ".",
        ESPALHADOR: "E",
        INATIVO: "N",
        INFLUENCIADOR: "I",
        BOT: "B",
        FACT_CHECKER: "F",
    }

    linhas = min(len(grade), limite)
    colunas = min(len(grade[0]), limite)

    for i in range(linhas):
        print(" ".join(simbolos[grade[i][j]] for j in range(colunas)))
    print()


def construir_bloco_com_halos(grade, duracoes, inicio, fim):
    """Monta um bloco com a linha anterior e a posterior como halo."""

    colunas = len(grade[0])
    bloco_grade = []
    bloco_duracoes = []

    if inicio > 0:
        bloco_grade.append(grade[inicio - 1][:])
        bloco_duracoes.append(duracoes[inicio - 1][:])
    else:
        bloco_grade.append([IGNORANTE] * colunas)
        bloco_duracoes.append([0] * colunas)

    for linha_grade, linha_duracao in zip(grade[inicio:fim], duracoes[inicio:fim]):
        bloco_grade.append(linha_grade[:])
        bloco_duracoes.append(linha_duracao[:])

    if fim < len(grade):
        bloco_grade.append(grade[fim][:])
        bloco_duracoes.append(duracoes[fim][:])
    else:
        bloco_grade.append([IGNORANTE] * colunas)
        bloco_duracoes.append([0] * colunas)

    return bloco_grade, bloco_duracoes


def processar_bloco_distribuido(bloco_grade, bloco_duracoes, limiar_convencimento, geracao, config):
    if len(bloco_grade) < 3:
        return [], []

    linhas_grade = []
    linhas_duracao = []

    for i in range(1, len(bloco_grade) - 1):
        linha, duracao = calcular_linha_proxima_geracao(
            bloco_grade,
            bloco_duracoes,
            i,
            limiar_convencimento,
            geracao,
            config,
        )
        linhas_grade.append(linha)
        linhas_duracao.append(duracao)

    return linhas_grade, linhas_duracao
