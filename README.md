# 📊 CorpTech ITSM Analytics

## 📌 Descrição do Projeto
O **CorpTech ITSM Analytics** é uma plataforma voltada para análise de dados de suporte de TI, utilizando informações extraídas do Jira Service Management (JSM) e transformadas em dashboards no Power BI por meio de uma arquitetura baseada em Azure.

---

**Integrantes:** Wellington Grein · Lucas Felipe · Pedro Placidina · Fellipe Prim
**Disciplina:** Design e Arquitetura de Software II — DAS II
*(projeto herdado de Tópicos Avançados em Programação — TAPR 2026/1)*

---

## Padrão de projeto aplicado: Command

### O problema

O projeto tem 11 Azure Functions. Dez delas carregam uma tabela da base de
origem para a base consolidada, e todas seguem **exatamente o mesmo algoritmo**:

1. montar a connection string da origem a partir das variáveis de ambiente
2. montar a connection string do destino
3. conectar na origem e fazer o `SELECT`
4. se não veio nada, encerrar
5. conectar no destino, ligar `IDENTITY_INSERT`
6. inserir registro a registro, ignorando os que já existem
7. desligar `IDENTITY_INSERT`, `commit` e registrar em log

A única coisa que muda de uma função para outra é **qual tabela** e **quais
colunas** — o resultado eram ~90 linhas praticamente idênticas copiadas 10
vezes. A décima primeira função (`extract_usr_users`) faz outra coisa: só lê
`dbo.usr_users` no banco de **destino** e joga o retorno no log.

Além da duplicação, havia um problema de arquitetura: **não existe ninguém
responsável por executar as cargas**. Cada trigger é um bloco solto que abre
conexão, monta SQL e trata erro por conta própria. Não há como logar todas de
forma uniforme, medir quanto cada uma demora, reprocessar uma que falhou ou
definir uma ordem entre elas — qualquer uma dessas mudanças custa 11 edições.

### A solução

O **Command** (padrão comportamental do GoF) transforma cada solicitação em um
objeto. Todas as solicitações passam a ter a mesma interface, `executar()`, e
um único objeto — o *Invoker* — passa a ser o responsável por dispará-las.

> *"Encapsular uma solicitação como um objeto, permitindo assim que você
> parametrize clientes com diferentes solicitações, enfileire ou registre (log)
> solicitações e suporte operações que podem ser desfeitas."*
> — GAMMA, HELM, JOHNSON, VLISSIDES (1994)

| Papel no padrão | No projeto |
|---|---|
| *Command* | `etl/comando.py` → `Comando` (interface: `nome`, `executar()`) |
| *ConcreteCommand* | `etl/comandos.py` → `CarregarTabela` e `ConsultarUsuarios` |
| *Receiver* | `etl/repositorio.py` → `RepositorioSql` (`ORIGEM` e `DESTINO`) |
| *Invoker* | `etl/comando.py` → `Agendador` |
| *Client* | `etl/catalogo.py` → cria os 11 comandos e registra no `AGENDADOR` |

Uma tabela nova agora custa **uma chamada** no catálogo:

```python
AGENDADOR.registrar(CarregarTabela(
    "itsm.fila",
    ["id_fila", "cd_fila", "nm_fila", "ds_descricao", "fl_ativo",
     "dt_inclusao", "dt_atualizacao", "nm_sistema_origem",
     "cd_registro_origem"],
))
```

E **todas** as 11 triggers ficaram com a mesma forma — só o agendamento e o
nome da solicitação:

```python
@app.timer_trigger(schedule="0 */30 * * * *", arg_name="myTimer",
                   run_on_startup=False, use_monitor=False)
def extract_fila(myTimer: func.TimerRequest) -> None:
    AGENDADOR.disparar("itsm.fila")
```

O `Agendador` não sabe o que cada comando faz — ele só conhece `executar()`.
É por isso que log de início/fim, medição de tempo e histórico de execução
valem para os 11 comandos de uma vez, escritos em um lugar só:

```python
def disparar(self, nome: str) -> None:
    comando = self._comandos.get(nome)
    ...
    logging.info("Iniciando: %s", nome)
    inicio = time.perf_counter()
    try:
        comando.executar()
    except Exception:
        self.historico.append((nome, "erro"))
        logging.exception("Erro na execução de %s", nome)
        raise
    self.historico.append((nome, "ok"))
    logging.info("Concluído: %s em %.2fs", nome, time.perf_counter() - inicio)
```

### Estrutura depois da refatoração

```
src/
├── function_app.py          registra os 11 blueprints (inalterado)
├── etl/
│   ├── conexao.py           connection strings em um único lugar
│   ├── repositorio.py       Receiver — RepositorioSql (ORIGEM / DESTINO)
│   ├── comando.py           Command (Comando) + Invoker (Agendador)
│   ├── comandos.py          ConcreteCommands — CarregarTabela, ConsultarUsuarios
│   └── catalogo.py          Client — monta e registra os 11 comandos
└── triggers/
    ├── extract_analista.py  só o @timer_trigger + AGENDADOR.disparar(...)
    └── ... (as 11, todas iguais)
```

### Consequências

**Positivas**

- **Uma interface para tudo.** As 11 solicitações têm a mesma assinatura.
  Quem dispara não precisa saber o que cada uma faz.
- **`extract_usr_users` entrou junto.** O algoritmo dela é diferente, mas o
  contrato é só `executar()` — ela virou `ConsultarUsuarios`, um comando como
  qualquer outro. A exceção deixou de ser exceção.
- **Passou a existir um responsável.** Log uniforme, tempo de execução e
  histórico ficam no `Agendador`. Reprocessar uma carga que falhou, enfileirar
  as cargas ou definir a ordem entre elas (carregar `fila` e `categoria` antes
  de `chamado`, que referencia as duas) passa a ser **uma** mudança, não 11.
- **Composição no lugar de herança.** Cada comando é independente; não existe
  classe base cuja alteração derrube as outras dez.
- De **951 para 491 linhas** de Python (−48%), sem perder nenhuma
  funcionalidade. Cada trigger caiu de ~90 para 11 linhas.
- A duplicação da connection string (22 blocos idênticos) desapareceu, e com
  ela o `logging.info` que gravava a **senha do banco em texto puro** — ela ia
  para o Application Insights em todas as 11 triggers.
- O SQL gerado é idêntico ao anterior, tabela por tabela (verificado).

**Negativas / trade-offs**

- **Mais classes e mais arquivos** para fazer o que antes era uma função.
  Em um projeto de 11 cargas, isso é um custo real de leitura.
- **Indireção:** quem abre `extract_fila.py` vê `AGENDADOR.disparar("itsm.fila")`
  e precisa percorrer `catalogo.py` → `comandos.py` → `repositorio.py` para
  entender o que acontece. Passamos de um arquivo longo para quatro curtos.
- **O Command não elimina duplicação por si só.** Se cada `ConcreteCommand`
  escrevesse o próprio `executar()`, voltaríamos às 10 cópias — agora em
  classes. Quem resolve a duplicação aqui é o fato de `CarregarTabela` ser
  **parametrizada**; o Command resolve a *orquestração*. Os dois problemas são
  diferentes e é honesto dizer isso.
- **Ligação por string.** `AGENDADOR.disparar("itsm.fila")` só falha em tempo
  de execução se o nome estiver errado — o `Agendador` levanta `KeyError` com a
  lista de comandos disponíveis, mas o compilador não ajuda.
- O `undo` que o padrão prevê **não** foi implementado: desfazer uma carga
  exigiria guardar o que foi inserido, e não há requisito para isso. Ficou como
  ponto de extensão, não como promessa.

---

## Sugestão de outro padrão: Strategy

Hoje `RepositorioSql.inserir()` implementa **uma única** política de carga:
`INSERT` registro a registro ignorando `IntegrityError`. Isso resolve duplicata,
mas nunca atualiza um registro que mudou na origem — e é lento, porque executa
um `INSERT` por linha.

O **Strategy** encapsularia a política de carga em objetos intercambiáveis:

```
CarregaStrategy (interface)
├── InsertIgnorandoDuplicados   ← comportamento atual
├── UpsertPorChave              ← MERGE: insere ou atualiza
└── TruncateEInsere             ← recarga completa da tabela
```

`CarregarTabela` receberia a estratégia como mais um parâmetro e delegaria a ela:

```python
AGENDADOR.registrar(CarregarTabela(
    "itsm.chamado", COLUNAS_CHAMADO, estrategia=UpsertPorChave(),
))
```

**Por que faz sentido aqui:** as tabelas têm necessidades diferentes. Dimensões
pequenas (`fila`, `categoria`, `sla`) mudam pouco e poderiam ser recarregadas
inteiras; `chamado` muda o tempo todo e precisaria de *upsert* para refletir
mudanças de status.

**O ponto de encaixe já existe:** o Command isolou o *o quê* (a solicitação) do
*quem executa* (o Receiver). O Strategy entra dentro do comando, para decidir o
*como*. É a evolução natural — o Command resolve "quem dispara e como
acompanhamos", o Strategy resolve "um passo precisa variar por tabela".
