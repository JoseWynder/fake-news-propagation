package basico;

import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class Worker {

    public static void main(String[] args) {
        try {
            // Conecta ao Master via RMI
            Registry registry = LocateRegistry.getRegistry("localhost", 1099);
            SimulacaoRMI master = (SimulacaoRMI) registry.lookup("FakeNewsMaster");

            int meuId = master.registrarWorker();
            int limiarConvencimento = 3; // Padrão da nossa simulação base

            System.out.println("Worker " + meuId + " pronto e aguardando fatias...");

            while (master.continuarSimulacao()) {
                
                // 1. Recebe a fatia bruta (já mastigada com as fronteiras/halos extras)
                int[][] loteComFronteiras = master.solicitarLoteComFronteiras(meuId);

                // 2. O Modelo assume o controle! (A mágica acontece em apenas 1 linha)
                int[][] loteProcessado = FakeNewsModelo.processarBlocoDistribuido(loteComFronteiras, limiarConvencimento);

                // 3. Devolve a fatia calculada para o Master
                master.enviarLoteProcessado(meuId, loteProcessado);
            }

            System.out.println("Worker " + meuId + " finalizou o processamento e está desligando.");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
