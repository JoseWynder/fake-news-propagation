import java.util.Locale;

public class FakeNewsSequencial {

    public static void main(String[] args) {
        Locale.setDefault(Locale.US);
        FakeNewsModelo.SimulationConfig config = FakeNewsModelo.SimulationConfig.fromArgs(args);
        int[][] grade = FakeNewsModelo.createGrid(config.linhas, config.colunas, config.percentual, config.semente);
        int totalCelulas = config.linhas * config.colunas;
        FakeNewsModelo.StateCount contagemInicial = FakeNewsModelo.countStates(grade);

        System.out.println("=== SIMULACAO SEQUENCIAL DE PROPAGACAO DE FAKE NEWS ===");
        System.out.println("Tamanho da grade: " + config.linhas + " x " + config.colunas + " (" + String.format("%,d", totalCelulas) + " pessoas)");
        System.out.println("Geracoes: " + config.geracoes);
        System.out.println("Percentual inicial de espalhadores: "
            + String.format(Locale.US, "%.2f", contagemInicial.espalhadores * 100.0 / totalCelulas)
            + "% (" + String.format("%,d", contagemInicial.espalhadores) + " espalhadores reais)");
        System.out.println("Limiar de convencimento: " + config.limiar + " vizinhos");
        System.out.println();

        long inicio = System.nanoTime();

        for (int geracao = 0; geracao < config.geracoes; geracao++) {
            grade = FakeNewsModelo.nextGenerationSequential(grade, config.limiar);
            FakeNewsModelo.StateCount contagem = FakeNewsModelo.countStates(grade);

            System.out.printf(
                Locale.US,
                "Geracao %03d | Ignorantes: %10s | Espalhadores: %10s | Inativos: %10s%n",
                geracao + 1,
                String.format("%,d", contagem.ignorantes),
                String.format("%,d", contagem.espalhadores),
                String.format("%,d", contagem.inativos)
            );

            if (contagem.espalhadores == 0) {
                System.out.println();
                System.out.println("A propagacao terminou: nao ha mais espalhadores.");
                break;
            }
        }

        double tempoTotal = (System.nanoTime() - inicio) / 1_000_000_000.0;
        FakeNewsModelo.StateCount contagemFinal = FakeNewsModelo.countStates(grade);

        System.out.println();
        System.out.println("=== RESULTADO FINAL ===");
        System.out.printf(Locale.US, "Tempo total de execucao: %.4f segundos%n", tempoTotal);
        System.out.printf(Locale.US, "Ignorantes finais: %,d (%.2f%%)%n", contagemFinal.ignorantes, contagemFinal.ignorantes * 100.0 / totalCelulas);
        System.out.printf(Locale.US, "Espalhadores finais: %,d (%.2f%%)%n", contagemFinal.espalhadores, contagemFinal.espalhadores * 100.0 / totalCelulas);
        System.out.printf(Locale.US, "Inativos finais: %,d (%.2f%%)%n", contagemFinal.inativos, contagemFinal.inativos * 100.0 / totalCelulas);
    }
}
