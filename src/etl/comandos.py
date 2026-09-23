import logging

from .comando import Comando
from .repositorio import DESTINO, ORIGEM


class CarregarTabela(Comando):
    def __init__(self, tabela: str, colunas: list,
                 usa_identity_insert: bool = True):
        self._tabela = tabela
        self._colunas = colunas
        self._usa_identity_insert = usa_identity_insert

    @property
    def nome(self) -> str:
        return self._tabela

    def executar(self) -> None:
        registros = ORIGEM.selecionar(self._tabela, self._colunas)

        if not registros:
            logging.info("Nenhum registro encontrado em %s.", self._tabela)
            return

        inseridos = DESTINO.inserir(
            self._tabela, self._colunas, registros, self._usa_identity_insert
        )

        logging.info("Carga de %s: %d de %d registros inseridos.",
                     self._tabela, inseridos, len(registros))
