package basico;

import java.util.Random;

public class FakeNewsModelo {

    public static final int IGNORANTE = 0;
    public static final int ESPALHADOR = 1;
    public static final int INATIVO = 2;

    // 1. Cria uma cópia profunda da matriz (Deep Copy)
    public static int[][] copiarGrade(int[][] grade) {
        int linhas = grade.length;
        int colunas = grade[0].length;
        int[][] novaGrade = new int[linhas][colunas];
        for (int i = 0; i < linhas; i++) {
            System.arraycopy(grade[i], 0, novaGrade[i], 0, colunas);
        }
        return novaGrade;
    }

    // 2. Cria a matriz inicial com espalhadores aleatórios
    public static int[][] criarGrade(int linhas, int colunas, double percentualEspalhadores, long semente) {
        Random rng = new Random(semente);
        int[][] grade = new int[linhas][colunas]; // Em Java, inteiros já inicializam com 0 (IGNORANTE)
        
        int totalCelulas = linhas * colunas;
        int totalEspalhadores = (int) (totalCelulas * percentualEspalhadores);

        if (totalEspalhadores <= 0) return grade;

        int colocados = 0;
        // Enquanto não atingir a cota, continua sorteando (evita colocar 2 no mesmo lugar)
        while (colocados < totalEspalhadores) {
            int i = rng.nextInt(linhas);
            int j = rng.nextInt(colunas);
            if (grade[i][j] == IGNORANTE) {
                grade[i][j] = ESPALHADOR;
                colocados++;
            }
        }
        return grade;
    }

    // 3. Conta espalhadores na vizinhança de Moore
    public static int contarVizinhosEspalhadores(int[][] grade, int i, int j) {
        int linhas = grade.length;
        int colunas = grade[0].length;
        int total = 0;

        for (int di = -1; di <= 1; di++) {
            for (int dj = -1; dj <= 1; dj++) {
                if (di == 0 && dj == 0) continue;

                int ni = i + di;
                int nj = j + dj;

                if (ni >= 0 && ni < linhas && nj >= 0 && nj < colunas) {
                    if (grade[ni][nj] == ESPALHADOR) {
                        total++;
                    }
                }
            }
        }
        return total;
    }

    // 4. Calcula uma linha da próxima geração a partir da grade atual
    public static int[] calcularLinhaProximaGeracao(int[][] grade, int i, int limiarConvencimento) {
        int colunas = grade[0].length;
        int[] novaLinha = new int[colunas];

        for (int j = 0; j < colunas; j++) {
            int estadoAtual = grade[i][j];

            if (estadoAtual == IGNORANTE) {
                int vizinhos = contarVizinhosEspalhadores(grade, i, j);
                novaLinha[j] = (vizinhos >= limiarConvencimento) ? ESPALHADOR : IGNORANTE;
            } else if (estadoAtual == ESPALHADOR) {
                novaLinha[j] = INATIVO;
            } else {
                novaLinha[j] = INATIVO;
            }
        }
        return novaLinha;
    }

    // 5. Divide o trabalho em fatias (Retorna matriz onde cada linha é [inicio, fim])
    public static int[][] dividirFaixas(int totalLinhas, int quantidadePartes) {
        if (totalLinhas <= 0) return new int[0][0];

        quantidadePartes = Math.max(1, Math.min(quantidadePartes, totalLinhas));
        int base = totalLinhas / quantidadePartes;
        int resto = totalLinhas % quantidadePartes;

        int[][] faixas = new int[quantidadePartes][2];
        int inicio = 0;

        for (int indice = 0; indice < quantidadePartes; indice++) {
            int tamanho = base + (indice < resto ? 1 : 0);
            int fim = inicio + tamanho;
            faixas[indice][0] = inicio;
            faixas[indice][1] = fim;
            inicio = fim;
        }
        return faixas;
    }

    // 6. Contagem de estados para o log (Retorna array: [Ignorantes, Espalhadores, Inativos])
    public static int[] contarEstados(int[][] grade) {
        int[] contagem = new int[3]; // [0] = IGNORANTE, [1] = ESPALHADOR, [2] = INATIVO
        for (int i = 0; i < grade.length; i++) {
            for (int j = 0; j < grade[0].length; j++) {
                contagem[grade[i][j]]++;
            }
        }
        return contagem;
    }

    // 7. Imprime parte da matriz no terminal
    public static void imprimirGrade(int[][] grade, int limite) {
        int linhas = Math.min(grade.length, limite);
        int colunas = Math.min(grade[0].length, limite);
        char[] simbolos = {'.', 'E', 'N'};

        for (int i = 0; i < linhas; i++) {
            StringBuilder sb = new StringBuilder();
            for (int j = 0; j < colunas; j++) {
                sb.append(simbolos[grade[i][j]]).append(" ");
            }
            System.out.println(sb.toString());
        }
        System.out.println();
    }

    // 8. (RMI) Monta o bloco com a linha de cima e de baixo extras (Halos)
    public static int[][] construirBlocoComHalos(int[][] grade, int inicio, int fim) {
        int colunas = grade[0].length;
        int tamanhoBloco = (fim - inicio) + 2; // +2 por causa dos halos
        int[][] bloco = new int[tamanhoBloco][colunas];

        // Halo Superior
        if (inicio > 0) {
            System.arraycopy(grade[inicio - 1], 0, bloco[0], 0, colunas);
        } else {
            // Preenche com 0 (IGNORANTE) se for a borda do mapa
            java.util.Arrays.fill(bloco[0], IGNORANTE);
        }

        // Miolo
        for (int i = inicio; i < fim; i++) {
            System.arraycopy(grade[i], 0, bloco[i - inicio + 1], 0, colunas);
        }

        // Halo Inferior
        if (fim < grade.length) {
            System.arraycopy(grade[fim], 0, bloco[tamanhoBloco - 1], 0, colunas);
        } else {
            java.util.Arrays.fill(bloco[tamanhoBloco - 1], IGNORANTE);
        }

        return bloco;
    }

    // 9. (RMI) Processa apenas o miolo do bloco recebido pelo Worker
    public static int[][] processarBlocoDistribuido(int[][] bloco, int limiarConvencimento) {
        if (bloco.length < 3) return new int[0][0];

        int linhasReais = bloco.length - 2;
        int[][] resultado = new int[linhasReais][bloco[0].length];

        for (int i = 1; i < bloco.length - 1; i++) {
            resultado[i - 1] = calcularLinhaProximaGeracao(bloco, i, limiarConvencimento);
        }

        return resultado;
    }
}
