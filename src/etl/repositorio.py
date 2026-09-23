import logging

import pyodbc

from .conexao import conectar_destino, conectar_origem


class RepositorioSql:
    def __init__(self, abrir_conexao, rotulo: str):
        self._abrir_conexao = abrir_conexao
        self._rotulo = rotulo

    def selecionar(self, tabela: str, colunas: list) -> list:
        sql = f"SELECT {', '.join(colunas)} FROM {tabela}"

        with self._abrir_conexao() as conexao:
            cursor = conexao.cursor()
            cursor.execute(sql)
            registros = [tuple(linha) for linha in cursor.fetchall()]

        logging.info("%d registros lidos de %s (%s).",
                     len(registros), tabela, self._rotulo)
        return registros

    def inserir(self, tabela: str, colunas: list, registros: list,
                identity_insert: bool = True) -> int:
        marcadores = ", ".join("?" * len(colunas))
        sql = (
            f"INSERT INTO {tabela} ({', '.join(colunas)}) "
            f"VALUES ({marcadores})"
        )

        inseridos = 0
        with self._abrir_conexao() as conexao:
            cursor = conexao.cursor()

            if identity_insert:
                cursor.execute(f"SET IDENTITY_INSERT {tabela} ON")

            for registro in registros:
                try:
                    cursor.execute(sql, registro)
                    inseridos += 1
                except pyodbc.IntegrityError:
                    pass

            if identity_insert:
                cursor.execute(f"SET IDENTITY_INSERT {tabela} OFF")

            conexao.commit()

        return inseridos


ORIGEM = RepositorioSql(conectar_origem, "origem")
DESTINO = RepositorioSql(conectar_destino, "destino")
