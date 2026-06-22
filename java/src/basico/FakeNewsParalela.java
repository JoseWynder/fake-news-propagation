package basico;

import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.BrokenBarrierException;

public class FakeNewsParalela {

    static int linhas = 1000;
    static int colunas = 1000;
    static int maxGeracoes = 50;
    static double percentualEspalhadores = 0.05;
    static int limiarConvencimento = 3;
    static int numThreads = 4;
    static long semente = 42L;

    static int[][] gradeAtual;
    static int[][] novaGrade;
    static int[][] faixasThreads;
    
    static boolean existemEspalhadores = true;
    static CyclicBarrier barreira;

    public static void main(String[] args) {
        // 1. Usa o modelo para inicializar a matriz e as faixas de divisão de carga
        gradeAtual = FakeNewsModelo.criarGrade(linhas, colunas, percentualEspalhadores, semente);
        novaGrade = new int[linhas][colunas];
        faixasThreads = FakeNewsModelo.dividirFaixas(linhas, numThreads);

        // Barreira que executa ao fim de cada geração (quando todas as threads terminarem)
        barreira = new CyclicBarrier(numThreads, () -> {
            int[][] temp = gradeAtual;
            gradeAtual = novaGrade;
            novaGrade = temp;

            int[] contagem = FakeNewsModelo.contarEstados(gradeAtual);
            existemEspalhadores = (contagem[FakeNewsModelo.ESPALHADOR] > 0);
        });

        System.out.println("=== SIMULAÇÃO PARALELA (THREADS - BÁSICO) ===");
        long inicioTempo = System.currentTimeMillis();

        Thread[] threads = new Thread[numThreads];

        // 2. Inicia as Threads
        for (int i = 0; i < numThreads; i++) {
            int threadId = i;
            threads[i] = new Thread(() -> executarTrabalhoThread(threadId));
            threads[i].start();
        }

        // Aguarda todas as threads finalizarem as 50 gerações
        for (int i = 0; i < numThreads; i++) {
            try { threads[i].join(); } catch (InterruptedException e) { e.printStackTrace(); }
        }

        long tempoTotal = System.currentTimeMillis() - inicioTempo;
        System.out.println("Tempo total de execução: " + (tempoTotal / 1000.0) + " segundos");
        
        // 3. Usa o modelo para o print final
        int[] contagemFinal = FakeNewsModelo.contarEstados(gradeAtual);
        System.out.println("Ignorantes finais: " + contagemFinal[FakeNewsModelo.IGNORANTE]);
        System.out.println("Espalhadores finais: " + contagemFinal[FakeNewsModelo.ESPALHADOR]);
        System.out.println("Inativos finais: " + contagemFinal[FakeNewsModelo.INATIVO]);
    }

    // A tarefa de cada Thread (Ficou incrivelmente limpo!)
    static void executarTrabalhoThread(int threadId) {
        int inicio = faixasThreads[threadId][0];
        int fim = faixasThreads[threadId][1];

        for (int g = 0; g < maxGeracoes && existemEspalhadores; g++) {
            
            // Cada thread varre apenas o seu bloco de linhas
            for (int i = inicio; i < fim; i++) {
                // Delega o cálculo pesado para o modelo
                novaGrade[i] = FakeNewsModelo.calcularLinhaProximaGeracao(gradeAtual, i, limiarConvencimento);
            }

            try {
                barreira.await(); // Espera os colegas terminarem a geração
            } catch (InterruptedException | BrokenBarrierException e) {
                e.printStackTrace();
            }
        }
    }
}
