import os

import pyodbc

_DRIVER = "ODBC Driver 18 for SQL Server"


def _connection_string(sufixo: str) -> str:
    return (
        f"DRIVER={{{_DRIVER}}};"
        f"SERVER={os.getenv(f'SQL_SERVER_{sufixo}')};"
        f"DATABASE={os.getenv(f'SQL_DATABASE_{sufixo}')};"
        f"UID={os.getenv(f'SQL_USER_{sufixo}')};"
        f"PWD={os.getenv(f'SQL_PASSWORD_{sufixo}')};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )


def conectar_origem() -> pyodbc.Connection:
    return pyodbc.connect(_connection_string("SOURCE"))


def conectar_destino() -> pyodbc.Connection:
    return pyodbc.connect(_connection_string("TARGET"))
