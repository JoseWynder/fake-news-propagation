import java.io.Serializable;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public final class FakeNewsModelo {

    public static final int IGNORANTE = 0;
    public static final int ESPALHADOR = 1;
    public static final int INATIVO = 2;

    private FakeNewsModelo() {
    }

    public static final class SimulationConfig implements Serializable {
        public int linhas = 500;
        public int colunas = 500;
        public int geracoes = 50;
        public double percentual = 0.02;
        public int limiar = 2;
        public long semente = 42L;
        public int threads = 4;

        public static SimulationConfig fromArgs(String[] args) {
            SimulationConfig config = new SimulationConfig();

            for (int i = 0; i < args.length; i++) {
                String argumento = args[i];
                if (!argumento.startsWith("--")) {
                    throw new IllegalArgumentException("Parametro invalido: " + argumento);
                }
                if (i + 1 >= args.length) {
                    throw new IllegalArgumentException("Valor ausente para: " + argumento);
                }

                String valor = args[++i];

                switch (argumento) {
                    case "--linhas":
                        config.linhas = Integer.parseInt(valor);
                        break;
                    case "--colunas":
                        config.colunas = Integer.parseInt(valor);
                        break;
                    case "--geracoes":
                        config.geracoes = Integer.parseInt(valor);
                        break;
                    case "--percentual":
                        config.percentual = Double.parseDouble(valor);
                        break;
                    case "--limiar":
                        config.limiar = Integer.parseInt(valor);
                        break;
                    case "--semente":
                        config.semente = Long.parseLong(valor);
                        break;
                    case "--threads":
                        config.threads = Integer.parseInt(valor);
                        break;
                    default:
                        throw new IllegalArgumentException("Parametro desconhecido: " + argumento);
                }
            }

            return config;
        }
    }

    public static final class StateCount {
        public int ignorantes;
        public int espalhadores;
        public int inativos;
    }

    public static int[][] createGrid(int linhas, int colunas, double percentualEspalhadores, long semente) {
        int[][] grade = createEmptyGrid(linhas, colunas);
        int totalCelulas = linhas * colunas;
        int totalEspalhadores = (int) (totalCelulas * percentualEspalhadores);

        if (totalEspalhadores <= 0) {
            return grade;
        }

        java.util.Random random = new java.util.Random(semente);
        Set<Integer> posicoes = new HashSet<>();

        while (posicoes.size() < totalEspalhadores) {
            posicoes.add(random.nextInt(totalCelulas));
        }

        for (int posicao : posicoes) {
            int linha = posicao / colunas;
            int coluna = posicao % colunas;
            grade[linha][coluna] = ESPALHADOR;
        }

        return grade;
    }

    public static int[][] createEmptyGrid(int linhas, int colunas) {
        return new int[linhas][colunas];
    }

    public static int[][] copyGrid(int[][] grade) {
        int[][] copia = new int[grade.length][grade[0].length];
        for (int i = 0; i < grade.length; i++) {
            copia[i] = Arrays.copyOf(grade[i], grade[i].length);
        }
        return copia;
    }

    public static int countSpreadersNeighbors(int[][] grade, int i, int j) {
        int linhas = grade.length;
        int colunas = grade[0].length;
        int total = 0;

        for (int di = -1; di <= 1; di++) {
            for (int dj = -1; dj <= 1; dj++) {
                if (di == 0 && dj == 0) {
                    continue;
                }

                int ni = i + di;
                int nj = j + dj;

                if (ni >= 0 && ni < linhas && nj >= 0 && nj < colunas && grade[ni][nj] == ESPALHADOR) {
                    total++;
                }
            }
        }

        return total;
    }

    public static int[] calculateNextRow(int[][] grade, int linha, int limiarConvencimento) {
        int[] novaLinha = Arrays.copyOf(grade[linha], grade[linha].length);

        for (int coluna = 0; coluna < grade[0].length; coluna++) {
            int estadoAtual = grade[linha][coluna];

            if (estadoAtual == IGNORANTE) {
                int vizinhos = countSpreadersNeighbors(grade, linha, coluna);
                novaLinha[coluna] = vizinhos >= limiarConvencimento ? ESPALHADOR : IGNORANTE;
            } else if (estadoAtual == ESPALHADOR) {
                novaLinha[coluna] = INATIVO;
            } else {
                novaLinha[coluna] = INATIVO;
            }
        }

        return novaLinha;
    }

    public static int[][] nextGenerationSequential(int[][] grade, int limiarConvencimento) {
        int[][] novaGrade = createEmptyGrid(grade.length, grade[0].length);
        for (int linha = 0; linha < grade.length; linha++) {
            novaGrade[linha] = calculateNextRow(grade, linha, limiarConvencimento);
        }
        return novaGrade;
    }

    public static StateCount countStates(int[][] grade) {
        StateCount contagem = new StateCount();

        for (int[] linha : grade) {
            for (int celula : linha) {
                if (celula == IGNORANTE) {
                    contagem.ignorantes++;
                } else if (celula == ESPALHADOR) {
                    contagem.espalhadores++;
                } else {
                    contagem.inativos++;
                }
            }
        }

        return contagem;
    }

    public static int[][] splitRanges(int totalLinhas, int quantidadePartes) {
        if (totalLinhas <= 0) {
            return new int[0][0];
        }

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
}
