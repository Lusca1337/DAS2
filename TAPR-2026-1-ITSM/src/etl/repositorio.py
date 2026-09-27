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


    def limpar(self, tabela: str) -> None:
        with self._abrir_conexao() as conexao:
            cursor = conexao.cursor()
            cursor.execute(f"DELETE FROM {tabela}")
            conexao.commit()

        logging.info("Tabela %s truncada (%s).", tabela, self._rotulo)

    def upsert(self, tabela: str, colunas: list, chave: str, registros: list,
               identity_insert: bool = True) -> int:
        indice_chave = colunas.index(chave)
        outras_colunas = [c for c in colunas if c != chave]

        set_clause = ", ".join(f"{coluna} = ?" for coluna in outras_colunas)
        sql = (
            f"MERGE {tabela} AS alvo "
            f"USING (SELECT ? AS {chave}) AS origem "
            f"ON alvo.{chave} = origem.{chave} "
            f"WHEN MATCHED THEN UPDATE SET {set_clause} "
            f"WHEN NOT MATCHED THEN INSERT ({', '.join(colunas)}) "
            f"VALUES ({', '.join('?' for _ in colunas)});"
        )

        afetados = 0
        with self._abrir_conexao() as conexao:
            cursor = conexao.cursor()

            if identity_insert:
                cursor.execute(f"SET IDENTITY_INSERT {tabela} ON")

            for registro in registros:
                valor_chave = registro[indice_chave]
                valores_update = [v for i, v in enumerate(registro) if i != indice_chave]
                parametros = [valor_chave] + valores_update + list(registro)
                cursor.execute(sql, parametros)
                afetados += cursor.rowcount

            if identity_insert:
                cursor.execute(f"SET IDENTITY_INSERT {tabela} OFF")

            conexao.commit()

        return afetados


ORIGEM = RepositorioSql(conectar_origem, "origem")
DESTINO = RepositorioSql(conectar_destino, "destino")