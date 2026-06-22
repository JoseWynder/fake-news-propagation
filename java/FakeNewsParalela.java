import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CyclicBarrier;
import java.util.Locale;

public class FakeNewsParalela {

    private static volatile int[][] gradeAtual;
    private static volatile int[][] novaGrade;
    private static volatile boolean existemEspalhadores = true;
    private static volatile int geracoesExecutadas = 0;

    public static void main(String[] args) {
        Locale.setDefault(Locale.US);
        FakeNewsModelo.SimulationConfig config = FakeNewsModelo.SimulationConfig.fromArgs(args);
        gradeAtual = FakeNewsModelo.createGrid(config.linhas, config.colunas, config.percentual, config.semente);
        novaGrade = FakeNewsModelo.createEmptyGrid(config.linhas, config.colunas);
        int totalCelulas = config.linhas * config.colunas;
        FakeNewsModelo.StateCount contagemInicial = FakeNewsModelo.countStates(gradeAtual);

        System.out.println("=== SIMULACAO PARALELA DE PROPAGACAO DE FAKE NEWS ===");
        System.out.println("Tamanho da grade: " + config.linhas + " x " + config.colunas + " (" + String.format("%,d", totalCelulas) + " pessoas)");
        System.out.println("Geracoes: " + config.geracoes);
        System.out.println("Percentual inicial de espalhadores: "
            + String.format(Locale.US, "%.2f", contagemInicial.espalhadores * 100.0 / totalCelulas)
            + "% (" + String.format("%,d", contagemInicial.espalhadores) + " espalhadores reais)");
        System.out.println("Limiar de convencimento: " + config.limiar + " vizinhos");
        System.out.println("Threads: " + config.threads);
        System.out.println();

        CyclicBarrier barreira = new CyclicBarrier(config.threads, () -> {
            int[][] temporaria = gradeAtual;
            gradeAtual = novaGrade;
            novaGrade = temporaria;
            geracoesExecutadas++;

            FakeNewsModelo.StateCount contagem = FakeNewsModelo.countStates(gradeAtual);
            System.out.printf(
                Locale.US,
                "Geracao %03d | Ignorantes: %10s | Espalhadores: %10s | Inativos: %10s%n",
                geracoesExecutadas,
                String.format("%,d", contagem.ignorantes),
                String.format("%,d", contagem.espalhadores),
                String.format("%,d", contagem.inativos)
            );

            existemEspalhadores = contagem.espalhadores > 0 && geracoesExecutadas < config.geracoes;
        });

        int[][] faixas = FakeNewsModelo.splitRanges(config.linhas, config.threads);
        Thread[] threads = new Thread[faixas.length];
        long inicio = System.nanoTime();

        for (int indice = 0; indice < faixas.length; indice++) {
            int linhaInicio = faixas[indice][0];
            int linhaFim = faixas[indice][1];
            threads[indice] = new Thread(new Worker(linhaInicio, linhaFim, config.limiar, config.geracoes, barreira));
            threads[indice].start();
        }

        for (Thread thread : threads) {
            try {
                thread.join();
            } catch (InterruptedException exc) {
                Thread.currentThread().interrupt();
                throw new RuntimeException("Execucao paralela interrompida.", exc);
            }
        }

        double tempoTotal = (System.nanoTime() - inicio) / 1_000_000_000.0;
        FakeNewsModelo.StateCount contagemFinal = FakeNewsModelo.countStates(gradeAtual);

        if (contagemFinal.espalhadores == 0) {
            System.out.println();
            System.out.println("A propagacao terminou: nao ha mais espalhadores.");
        }

        System.out.println();
        System.out.println("=== RESULTADO FINAL ===");
        System.out.printf(Locale.US, "Tempo total de execucao: %.4f segundos%n", tempoTotal);
        System.out.printf(Locale.US, "Ignorantes finais: %,d (%.2f%%)%n", contagemFinal.ignorantes, contagemFinal.ignorantes * 100.0 / totalCelulas);
        System.out.printf(Locale.US, "Espalhadores finais: %,d (%.2f%%)%n", contagemFinal.espalhadores, contagemFinal.espalhadores * 100.0 / totalCelulas);
        System.out.printf(Locale.US, "Inativos finais: %,d (%.2f%%)%n", contagemFinal.inativos, contagemFinal.inativos * 100.0 / totalCelulas);
    }

    private static final class Worker implements Runnable {
        private final int linhaInicio;
        private final int linhaFim;
        private final int limiar;
        private final int maxGeracoes;
        private final CyclicBarrier barreira;

        private Worker(int linhaInicio, int linhaFim, int limiar, int maxGeracoes, CyclicBarrier barreira) {
            this.linhaInicio = linhaInicio;
            this.linhaFim = linhaFim;
            this.limiar = limiar;
            this.maxGeracoes = maxGeracoes;
            this.barreira = barreira;
        }

        @Override
        public void run() {
            while (existeTrabalho()) {
                for (int linha = linhaInicio; linha < linhaFim; linha++) {
                    novaGrade[linha] = FakeNewsModelo.calculateNextRow(gradeAtual, linha, limiar);
                }

                try {
                    barreira.await();
                } catch (InterruptedException exc) {
                    Thread.currentThread().interrupt();
                    return;
                } catch (BrokenBarrierException exc) {
                    throw new RuntimeException("Falha de sincronizacao entre threads.", exc);
                }
            }
        }

        private boolean existeTrabalho() {
            return existemEspalhadores && geracoesExecutadas < maxGeracoes;
        }
    }
}
