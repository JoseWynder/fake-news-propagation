import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class FakeNewsBenchmark {

    private static final Pattern TEMPO_PATTERN = Pattern.compile("Tempo total de execucao: ([0-9]+\\.[0-9]+) segundos");
    private static final Pattern IGNORANTES_PATTERN = Pattern.compile("Ignorantes finais: ([0-9,]+)");
    private static final Pattern ESPALHADORES_PATTERN = Pattern.compile("Espalhadores finais: ([0-9,]+)");
    private static final Pattern INATIVOS_PATTERN = Pattern.compile("Inativos finais: ([0-9,]+)");

    private static final class ProcessResult {
        private final int exitCode;
        private final String output;

        private ProcessResult(int exitCode, String output) {
            this.exitCode = exitCode;
            this.output = output;
        }
    }

    private static final class SimulationResult {
        private final double tempo;
        private final int ignorantes;
        private final int espalhadores;
        private final int inativos;
        private final String output;

        private SimulationResult(double tempo, int ignorantes, int espalhadores, int inativos, String output) {
            this.tempo = tempo;
            this.ignorantes = ignorantes;
            this.espalhadores = espalhadores;
            this.inativos = inativos;
            this.output = output;
        }
    }

    public static void main(String[] args) throws Exception {
        Locale.setDefault(Locale.US);
        FakeNewsModelo.SimulationConfig config = FakeNewsModelo.SimulationConfig.fromArgs(args);
        Path workdir = Path.of(".").toAbsolutePath().normalize();

        SimulationResult sequencial = executarSimples(workdir, "FakeNewsSequencial", buildCommonArgs(config));
        SimulationResult paralela = executarSimples(workdir, "FakeNewsParalela", buildParallelArgs(config));

        validarResultados(sequencial, paralela, "paralela");

        double speedupParalela = sequencial.tempo / paralela.tempo;
        double eficienciaParalela = speedupParalela / Math.max(1, config.threads);

        System.out.println("=== COMPARACAO DE DESEMPENHO ===");
        System.out.printf(Locale.US, "Sequencial : %.4f s%n", sequencial.tempo);
        System.out.printf(Locale.US, "Paralela   : %.4f s | speedup = %.2f | eficiencia = %.2f%n",
            paralela.tempo, speedupParalela, eficienciaParalela);
    }

    private static List<String> buildCommonArgs(FakeNewsModelo.SimulationConfig config) {
        List<String> args = new ArrayList<>();
        args.add("--linhas");
        args.add(String.valueOf(config.linhas));
        args.add("--colunas");
        args.add(String.valueOf(config.colunas));
        args.add("--geracoes");
        args.add(String.valueOf(config.geracoes));
        args.add("--percentual");
        args.add(String.valueOf(config.percentual));
        args.add("--limiar");
        args.add(String.valueOf(config.limiar));
        args.add("--semente");
        args.add(String.valueOf(config.semente));
        return args;
    }

    private static List<String> buildParallelArgs(FakeNewsModelo.SimulationConfig config) {
        List<String> args = buildCommonArgs(config);
        args.add("--threads");
        args.add(String.valueOf(config.threads));
        return args;
    }

    private static SimulationResult executarSimples(Path workdir, String classePrincipal, List<String> argumentos) throws Exception {
        List<String> comando = new ArrayList<>();
        comando.add("java");
        comando.add("-cp");
        comando.add(".");
        comando.add(classePrincipal);
        comando.addAll(argumentos);

        ProcessResult resultado = runProcess(workdir, comando);
        if (resultado.exitCode != 0) {
            throw new IllegalStateException("Falha ao executar " + classePrincipal + ":\n" + resultado.output);
        }
        return parseSimulationResult(resultado.output);
    }

    private static void validarResultados(SimulationResult base, SimulationResult atual, String nomeVersao) {
        if (base.ignorantes != atual.ignorantes || base.espalhadores != atual.espalhadores || base.inativos != atual.inativos) {
            throw new IllegalStateException(
                "A versao " + nomeVersao + " nao preservou o estado final da sequencial.\n"
                    + "Sequencial: " + base.ignorantes + "/" + base.espalhadores + "/" + base.inativos + "\n"
                    + "Atual: " + atual.ignorantes + "/" + atual.espalhadores + "/" + atual.inativos
            );
        }
    }

    private static SimulationResult parseSimulationResult(String output) {
        double tempo = extractDouble(output, TEMPO_PATTERN, "tempo total");
        int ignorantes = extractInt(output, IGNORANTES_PATTERN, "ignorantes finais");
        int espalhadores = extractInt(output, ESPALHADORES_PATTERN, "espalhadores finais");
        int inativos = extractInt(output, INATIVOS_PATTERN, "inativos finais");
        return new SimulationResult(tempo, ignorantes, espalhadores, inativos, output);
    }

    private static double extractDouble(String output, Pattern pattern, String label) {
        Matcher matcher = pattern.matcher(output);
        if (!matcher.find()) {
            throw new IllegalStateException("Nao foi possivel localizar " + label + " na saida:\n" + output);
        }
        return Double.parseDouble(matcher.group(1));
    }

    private static int extractInt(String output, Pattern pattern, String label) {
        Matcher matcher = pattern.matcher(output);
        if (!matcher.find()) {
            throw new IllegalStateException("Nao foi possivel localizar " + label + " na saida:\n" + output);
        }
        return Integer.parseInt(matcher.group(1).replace(",", ""));
    }

    private static ProcessResult runProcess(Path workdir, List<String> comando) throws Exception {
        ProcessCapture captura = startProcess(workdir, comando);
        int exitCode = captura.process.waitFor();
        captura.thread.join();
        return new ProcessResult(exitCode, captura.buffer.toString());
    }

    private static ProcessCapture startProcess(Path workdir, List<String> comando) throws IOException {
        ProcessBuilder builder = new ProcessBuilder(comando);
        builder.directory(workdir.toFile());
        builder.redirectErrorStream(true);

        Process process = builder.start();
        StringBuilder buffer = new StringBuilder();
        Thread thread = new Thread(() -> consumeOutput(process, buffer));
        thread.setDaemon(true);
        thread.start();
        return new ProcessCapture(process, thread, buffer);
    }

    private static void consumeOutput(Process process, StringBuilder buffer) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
            String linha;
            while ((linha = reader.readLine()) != null) {
                buffer.append(linha).append(System.lineSeparator());
            }
        } catch (IOException exc) {
            buffer.append("ERRO AO LER SAIDA: ").append(exc.getMessage()).append(System.lineSeparator());
        }
    }

    private static final class ProcessCapture {
        private final Process process;
        private final Thread thread;
        private final StringBuilder buffer;

        private ProcessCapture(Process process, Thread thread, StringBuilder buffer) {
            this.process = process;
            this.thread = thread;
            this.buffer = buffer;
        }
    }
}
