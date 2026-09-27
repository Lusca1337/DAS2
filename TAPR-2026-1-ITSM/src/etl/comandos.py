import logging

from .comando import Comando
from .estrategia_carga import CargaStrategy, InsertIgnorandoDuplicados
from .repositorio import DESTINO, ORIGEM


class CarregarTabela(Comando):
    def __init__(self, tabela: str, colunas: list,
                 usa_identity_insert: bool = True,
                 estrategia: CargaStrategy = None):
        self._tabela = tabela
        self._colunas = colunas
        self._usa_identity_insert = usa_identity_insert
        self._estrategia = estrategia or InsertIgnorandoDuplicados()

    @property
    def nome(self) -> str:
        return self._tabela

    def executar(self) -> None:
        registros = ORIGEM.selecionar(self._tabela, self._colunas)

        if not registros:
            logging.info("Nenhum registro encontrado em %s.", self._tabela)
            return

        afetados = self._estrategia.carregar(
            DESTINO, self._tabela, self._colunas, registros,
            self._usa_identity_insert,
        )

        logging.info("Carga de %s: %d de %d registros afetados.",
                     self._tabela, afetados, len(registros))