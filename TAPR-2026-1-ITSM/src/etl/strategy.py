from abc import ABC, abstractmethod

class CargaStrategy(ABC):
    @abstractmethod
    def carregar(self, repositorio, tabela: str, colunas: list,
                 registros: list, identity_insert: bool) -> int:
        ...


class InsertIgnorandoDuplicados(CargaStrategy):
    def carregar(self, repositorio, tabela, colunas, registros, identity_insert):
        return repositorio.inserir(tabela, colunas, registros, identity_insert)


class UpsertPorChave(CargaStrategy):
    def carregar(self, repositorio, tabela, colunas, registros, identity_insert):
        chave = colunas[0]
        return repositorio.upsert(tabela, colunas, chave, registros, identity_insert)


class TruncateEInsere(CargaStrategy):
    def carregar(self, repositorio, tabela, colunas, registros, identity_insert):
        repositorio.limpar(tabela)
        return repositorio.inserir(tabela, colunas, registros, identity_insert)