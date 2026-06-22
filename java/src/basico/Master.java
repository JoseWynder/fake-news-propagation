package basico;

import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;
import java.rmi.RemoteException;

public class Master implements SimulacaoRMI {

    private int linhas = 1000;
    private int colunas = 1000;
    private int maxGeracoes = 50;
    private double percentualEspalhadores = 0.05;
    private long semente = 42L;

    private int totalWorkersEsperados;
    private int workersRegistrados = 0;
    private int workersFinalizados = 0;
    
    private int geracaoAtual = 0;
    private boolean existemEspalhadores = true;

    private int[][] gradeGlobal;
    private int[][] novaGradeGlobal;
    private int[][] faixasWorkers; // Guarda [inicio, fim] da responsabilidade de cada worker

    public Master(int totalWorkers) {
        this.totalWorkersEsperados = totalWorkers;
        
        // 1. Usa o modelo para criar a grade com a mesma Semente (Paridade total com Python)
        this.gradeGlobal = FakeNewsModelo.criarGrade(linhas, colunas, percentualEspalhadores, semente);
        this.novaGradeGlobal = new int[linhas][colunas];
        
        // 2. Usa o modelo para dividir o trabalho e guardar as faixas
        this.faixasWorkers = FakeNewsModelo.dividirFaixas(linhas, totalWorkersEsperados);
    }

    @Override
    public synchronized int registrarWorker() throws RemoteException {
        int id = workersRegistrados++;
        System.out.println("Worker " + id + " registrado na rede.");
        return id;
    }

    @Override
    public synchronized int[][] solicitarLoteComFronteiras(int workerId) throws RemoteException {
        if (workerId >= faixasWorkers.length) return new int[0][0];

        int inicio = faixasWorkers[workerId][0];
        int fim = faixasWorkers[workerId][1];

        // 3. Usa o modelo para montar a fatia com o Halo Superior e Inferior
        return FakeNewsModelo.construirBlocoComHalos(gradeGlobal, inicio, fim);
    }

    @Override
    public synchronized void enviarLoteProcessado(int workerId, int[][] loteProcessado) throws RemoteException {
        int inicio = faixasWorkers[workerId][0];

        // Cola a fatia processada na nova matriz global
        for (int i = 0; i < loteProcessado.length; i++) {
            novaGradeGlobal[inicio + i] = loteProcessado[i];
        }

        workersFinalizados++;

        // Barreira de Sincronização: Se todos entregaram, avança a geração!
        if (workersFinalizados == totalWorkersEsperados) {
            
            // Troca os ponteiros (O(1)) em vez de usar deepcopy para garantir altíssimo desempenho em Java
            int[][] temp = gradeGlobal;
            gradeGlobal = novaGradeGlobal;
            novaGradeGlobal = temp;

            // 4. Usa o modelo para auditar os resultados da geração
            int[] contagem = FakeNewsModelo.contarEstados(gradeGlobal);
            existemEspalhadores = (contagem[FakeNewsModelo.ESPALHADOR] > 0);

            geracaoAtual++;
            workersFinalizados = 0;
            
            System.out.println("Geração " + geracaoAtual + " | Ignorantes: " + contagem[FakeNewsModelo.IGNORANTE] + 
                               " | Espalhadores: " + contagem[FakeNewsModelo.ESPALHADOR] + 
                               " | Inativos: " + contagem[FakeNewsModelo.INATIVO]);
            
            // Acorda todos os Workers que estavam bloqueados
            notifyAll(); 
        } else {
            try {
                wait(); // Worker dorme até o último chegar
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    @Override
    public synchronized boolean continuarSimulacao() throws RemoteException {
        return geracaoAtual < maxGeracoes && existemEspalhadores;
    }

    public static void main(String[] args) {
        try {
            int numWorkers = 4; // Lembrete: Tem que iniciar 4 workers no terminal
            Master servidor = new Master(numWorkers);
            
            SimulacaoRMI stub = (SimulacaoRMI) UnicastRemoteObject.exportObject(servidor, 0);
            Registry registry = LocateRegistry.createRegistry(1099);
            registry.rebind("FakeNewsMaster", stub);
            
            System.out.println("=== MASTER INICIADO (VERSÃO BÁSICA) ===");
            System.out.println("Matriz: 1000x1000 | Semente: 42");
            System.out.println("Aguardando " + numWorkers + " conexões RMI na porta 1099...");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
