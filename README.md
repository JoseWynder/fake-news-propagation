# Fake News

Projeto desenvolvido para a disciplina de Sistemas Distribuidos.

A proposta do trabalho consiste em transformar uma simulacao sequencial de propagacao de fake news em versoes paralela e distribuida, alem de comparar o comportamento e o desempenho das diferentes abordagens. O repositorio reune a implementacao principal em Python e uma implementacao complementar em Java, ambas com suporte a benchmark para facilitar a execucao dos experimentos.

---

## Objetivos do Projeto

O projeto foi desenvolvido com os seguintes objetivos:

* implementar a simulacao sequencial da propagacao de fake news;
* evoluir a solucao para uma versao paralela;
* evoluir a solucao para uma versao distribuida;
* comparar o desempenho entre as diferentes abordagens;
* adicionar melhorias e extensoes ao modelo original.

---

## Modelo da Simulacao

A simulacao representa a populacao como uma matriz bidimensional.

Cada posicao da matriz representa um individuo, e a propagacao ocorre localmente em geracoes discretas usando a vizinhanca de Moore, ou seja, considerando ate 8 vizinhos ao redor de cada celula.

Nas versoes paralela e distribuida, o comportamento logico da simulacao e preservado em relacao a versao sequencial, alterando apenas a forma como o processamento interno da proxima geracao e dividido.

### Estados basicos

* `0` = ignorante
* `1` = espalhador
* `2` = inativo

### Estados adicionais das melhorias

* `3` = influenciador
* `4` = bot
* `5` = fact-checker

---

## Organizacao do Repositorio

| Caminho | Responsabilidade |
| ------- | ---------------- |
| `python/` | Implementacao principal do projeto, com versoes sequencial, paralela, distribuida e benchmark |
| `java/` | Implementacao complementar do projeto, com versoes sequencial, paralela e benchmark |
| `README.md` | Documentacao principal do repositorio |

---

## Tecnologias Utilizadas

* Python
* Java
* Threads
* Sockets TCP

---

## Implementacoes do Projeto

### Python

A versao em Python e a implementacao principal do projeto e contem:

* versao sequencial;
* versao paralela com `threads`;
* versao distribuida com `sockets`;
* worker dedicado para a versao distribuida;
* modelo compartilhado da simulacao;
* geracao opcional de graficos da curva da simulacao;
* benchmark para comparacao entre as versoes.

Na versao paralela, a matriz e dividida em faixas continuas de linhas, e cada thread calcula apenas sua propria faixa da proxima geracao. Isso ajuda a manter consistencia entre geracoes e evita condicoes de corrida.

Na versao distribuida, a matriz tambem e dividida por faixas de linhas, mas cada bloco e enviado para um worker via socket. Alem das linhas principais, o worker recebe as fronteiras necessarias para calcular corretamente a vizinhanca de Moore nas bordas do bloco.

### Java

A versao em Java foi mantida como implementacao complementar, com foco nas versoes locais e na comparacao entre sequencial e paralela.

---

## Melhorias Implementadas

Além da simulacao base, a versao Python recebeu melhorias opcionais no modelo:

* probabilidade de convencimento;
* influenciadores digitais;
* bots automatizados;
* resistencia a propagacao com fact-checkers;
* estatisticas adicionais por geracao;
* geracao opcional de graficos da simulacao.

Essas melhorias foram implementadas de forma opcional, ou seja, o comportamento original continua preservado quando os novos parametros nao sao informados.

---

## Execucao

Os comandos abaixo devem ser executados a partir das respectivas pastas.

### Python

#### Sequencial

```bash
python FakeNewsSequencial.py --linhas 500 --colunas 500 --geracoes 50 --percentual 0.02 --limiar 2
```

#### Paralela

```bash
python FakeNewsParalela.py --linhas 500 --colunas 500 --geracoes 50 --percentual 0.02 --limiar 2 --threads 4
```

#### Worker da versao distribuida

Abra um terminal para cada worker:

```bash
python FakeNewsWorker.py --host 0.0.0.0 --port 5001
python FakeNewsWorker.py --host 0.0.0.0 --port 5002
```

#### Distribuida

Com os workers ja abertos:

```bash
python FakeNewsDistribuida.py --linhas 500 --colunas 500 --geracoes 50 --percentual 0.02 --limiar 2 --workers 127.0.0.1:5001 127.0.0.1:5002
```

#### Benchmark

```bash
python FakeNewsBenchmark.py --linhas 500 --colunas 500 --geracoes 50 --percentual 0.02 --limiar 2 --threads 4 --workers 127.0.0.1:5001 127.0.0.1:5002
```

#### Exemplo com melhorias ativadas

```bash
python FakeNewsSequencial.py --linhas 500 --colunas 500 --geracoes 50 --percentual 0.02 --limiar 2 --chance-convencimento 0.6 --percentual-influenciadores 0.01 --peso-influenciador 2 --vida-influenciador 3 --percentual-bots 0.01 --percentual-fact-checkers 0.01 --peso-fact-checker 2 --gerar-grafico
```

### Java

Entre na pasta `java/` e compile os arquivos:

```bash
javac *.java
```

#### Sequencial

```bash
java -cp . FakeNewsSequencial --linhas 500 --colunas 500 --geracoes 50 --percentual 0.02 --limiar 2 --semente 42
```

#### Paralela

```bash
java -cp . FakeNewsParalela --linhas 500 --colunas 500 --geracoes 50 --percentual 0.02 --limiar 2 --semente 42 --threads 4
```

#### Benchmark

```bash
java -cp . FakeNewsBenchmark --linhas 500 --colunas 500 --geracoes 50 --percentual 0.02 --limiar 2 --semente 42 --threads 4
```

---

## Parametros Principais da Versao Python

| Parametro | Descricao |
| --------- | --------- |
| `--linhas` | Numero de linhas da matriz |
| `--colunas` | Numero de colunas da matriz |
| `--geracoes` | Limite de geracoes da simulacao |
| `--percentual` | Percentual inicial de espalhadores |
| `--limiar` | Numero minimo de vizinhos para convencimento |
| `--threads` | Quantidade de threads da versao paralela |
| `--workers` | Lista de `host:porta` da versao distribuida |
| `--chance-convencimento` | Probabilidade de convencimento apos atingir o limiar |
| `--percentual-influenciadores` | Percentual inicial de influenciadores |
| `--peso-influenciador` | Peso dos influenciadores na vizinhanca |
| `--vida-influenciador` | Quantidade de geracoes em que o influenciador permanece ativo |
| `--percentual-bots` | Percentual inicial de bots |
| `--percentual-fact-checkers` | Percentual inicial de fact-checkers |
| `--peso-fact-checker` | Peso negativo dos fact-checkers |
| `--gerar-grafico` | Gera um grafico `.png` ao final da simulacao |

---

## Observacoes

* a versao Python e a linha principal do projeto;
* a versao Java foi mantida como implementacao complementar;
* a geracao de graficos na versao Python depende da biblioteca `matplotlib`;
* a versao distribuida em Python exige workers ativos antes da execucao do mestre;
* os benchmarks automatizam a comparacao entre as implementacoes disponiveis em cada linguagem.

---

## Integrantes

* JOSE WYNDER ALVES HERNANDES
* JOÃO LUCAS SILVA DE SOUZA
* 
* 
