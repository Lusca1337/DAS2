import logging
import time
from abc import ABC, abstractmethod


class Comando(ABC):
    @property
    @abstractmethod
    def nome(self) -> str:
        """Identificador da solicitação. Exemplo: ``"itsm.analista"``."""

    @abstractmethod
    def executar(self) -> None:
        """Executa a solicitação delegando ao Receiver."""


class ComandoComposto(Comando):
    def __init__(self, nome: str, comandos: list):
        self._nome = nome
        self._comandos = list(comandos)

    @property
    def nome(self) -> str:
        return self._nome

    def __len__(self) -> int:
        return len(self._comandos)

    def executar(self) -> None:
        total = len(self._comandos)
        for posicao, comando in enumerate(self._comandos, start=1):
            logging.info("[%d/%d] %s", posicao, total, comando.nome)
            comando.executar()


class Agendador:
    def __init__(self):
        self._comandos: dict = {}
        self.historico: list = []

    def registrar(self, comando: Comando) -> "Agendador":
        if comando.nome in self._comandos:
            raise ValueError(f"Comando já registrado: {comando.nome}")
        self._comandos[comando.nome] = comando
        return self

    def registrados(self) -> list:
        return sorted(self._comandos)

    def disparar(self, nome: str) -> None:
        comando = self._comandos.get(nome)
        if comando is None:
            raise KeyError(
                f"Comando não registrado: {nome}. "
                f"Disponíveis: {', '.join(self.registrados())}"
            )

        logging.info("Iniciando: %s", nome)
        inicio = time.perf_counter()
        try:
            comando.executar()
        except Exception:
            self.historico.append((nome, "erro"))
            logging.exception("Erro na execução de %s", nome)
            raise

        decorrido = time.perf_counter() - inicio
        self.historico.append((nome, "ok"))
        logging.info("Concluído: %s em %.2fs", nome, decorrido)
