package basico;

import java.rmi.Remote;
import java.rmi.RemoteException;

public interface SimulacaoRMI extends Remote {
    
    // O Worker se apresenta ao Master e recebe um ID único
    int registrarWorker() throws RemoteException;
    
    // O Worker pede sua fatia (agora a montagem dos Halos é feita pelo Modelo lá no Master)
    int[][] solicitarLoteComFronteiras(int workerId) throws RemoteException;
    
    // O Worker devolve a fatia já calculada
    void enviarLoteProcessado(int workerId, int[][] loteProcessado) throws RemoteException;
    
    // Verifica se a simulação deve continuar
    boolean continuarSimulacao() throws RemoteException;
}
