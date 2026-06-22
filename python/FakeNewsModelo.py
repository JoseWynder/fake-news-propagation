"""Modelo compartilhado da simulacao de fake news.

Este modulo reune a logica de regra e manipulacao da grade.
Nao tem dependencia de threads ou sockets.
"""

from __future__ import annotations

import random

IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2


def copiar_grade(grade):
    # Cria uma copia por linha para manter cada geracao isolada
    return [linha[:] for linha in grade]


def criar_grade(linhas, colunas, percentual_espalhadores=0.02, semente=42):
    """Cria uma grade deterministica com espalhadores iniciais"""

    rng = random.Random(semente)
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]

    total_celulas = linhas * colunas
    total_espalhadores = int(total_celulas * percentual_espalhadores)

    if total_espalhadores <= 0:
        return grade

    # A escolha sem repeticao garante a quantidade
    for posicao in rng.sample(range(total_celulas), total_espalhadores):
        i, j = divmod(posicao, colunas)
        grade[i][j] = ESPALHADOR

    return grade


def contar_vizinhos_espalhadores(grade, i, j):
    """Conta espalhadores na vizinhanca de Moore."""

    linhas = len(grade)
    colunas = len(grade[0])
    total = 0

    # Varrimento local dos 8 vizinhos ao redor da celula atual.
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue

            ni = i + di
            nj = j + dj

            if 0 <= ni < linhas and 0 <= nj < colunas:
                if grade[ni][nj] == ESPALHADOR:
                    total += 1

    return total


def calcular_linha_proxima_geracao(grade, i, limiar_convencimento):
    """Calcula uma linha da proxima geracao a partir da grade atual."""

    nova_linha = grade[i][:]

    for j in range(len(grade[0])):
        estado_atual = grade[i][j]

        # A regra sempre usa a geracao anterior como referencia
        if estado_atual == IGNORANTE:
            vizinhos = contar_vizinhos_espalhadores(grade, i, j)
            nova_linha[j] = ESPALHADOR if vizinhos >= limiar_convencimento else IGNORANTE
        elif estado_atual == ESPALHADOR:
            nova_linha[j] = INATIVO
        else:
            nova_linha[j] = INATIVO

    return nova_linha


def proxima_geracao_sequencial(grade, limiar_convencimento=2):
    # A versao sequencial calcula linha por linha em uma nova matriz
    return [calcular_linha_proxima_geracao(grade, i, limiar_convencimento) for i in range(len(grade))]


def dividir_faixas(total_linhas, quantidade_partes):
    # Divide o trabalho em blocos adjacentes de linhas.
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
    # Retorna um resumo simples da populacao por estado.
    contagem = {
        IGNORANTE: 0,
        ESPALHADOR: 0,
        INATIVO: 0,
    }

    for linha in grade:
        for celula in linha:
            contagem[celula] += 1

    return contagem


def imprimir_grade(grade, limite=30):
    # Impressao parcial para nao poluir o terminal em grades maiores
    simbolos = {
        IGNORANTE: ".",
        ESPALHADOR: "E",
        INATIVO: "N",
    }

    linhas = min(len(grade), limite)
    colunas = min(len(grade[0]), limite)

    for i in range(linhas):
        print(" ".join(simbolos[grade[i][j]] for j in range(colunas)))
    print()


def construir_bloco_com_halos(grade, inicio, fim):
    """Monta um bloco com a linha anterior e a posterior como halo."""

    colunas = len(grade[0])
    bloco = []

    # O halo superior e inferior permitem calcular a vizinhanca nas bordas.
    if inicio > 0:
        bloco.append(grade[inicio - 1][:])
    else:
        bloco.append([IGNORANTE] * colunas)

    for linha in grade[inicio:fim]:
        bloco.append(linha[:])

    if fim < len(grade):
        bloco.append(grade[fim][:])
    else:
        bloco.append([IGNORANTE] * colunas)

    return bloco


def processar_bloco_distribuido(bloco, limiar_convencimento):
    # O worker processa apenas as linhas centrais do bloco recebido.
    if len(bloco) < 3:
        return []

    return [
        calcular_linha_proxima_geracao(bloco, i, limiar_convencimento)
        for i in range(1, len(bloco) - 1)
    ]
