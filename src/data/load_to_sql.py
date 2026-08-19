from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
FEATURES_PATH = ROOT / "data" / "processed" / "features.csv"
DB_PATH = ROOT / "sompo.db"
TABLE_NAME = "telemetria"


def carregar_equipamentos(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    colunas = conn.execute("PRAGMA table_info(equipamentos)").fetchall()
    if not colunas:
        return

    equipamentos = (
        df.groupby("id_equipamento")
        .agg(
            tipo_equipamento=("tipo_equipamento", "first"),
            latitude_base=("latitude", "mean"),
            longitude_base=("longitude", "mean"),
        )
        .reset_index()
    )
    equipamentos["estado_uf"] = equipamentos["id_equipamento"].str.split("-").str[1]
    equipamentos["ano_fabricacao"] = 2020
    equipamentos["capacidade_carga_kg"] = equipamentos["tipo_equipamento"].map(
        {"Colheitadeira": 15000, "Trator": 8000, "Pulverizador": 5000}
    )
    dados = equipamentos[
        [
            "id_equipamento",
            "tipo_equipamento",
            "estado_uf",
            "latitude_base",
            "longitude_base",
            "ano_fabricacao",
            "capacidade_carga_kg",
        ]
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO equipamentos
            (id_equipamento, tipo_equipamento, estado_uf, latitude_base, longitude_base, ano_fabricacao, capacidade_carga_kg)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        dados.itertuples(index=False, name=None),
    )


def obter_colunas_tabela(conn: sqlite3.Connection) -> list[str]:
    colunas = conn.execute(f"PRAGMA table_info({TABLE_NAME})").fetchall()
    if not colunas:
        raise RuntimeError(f"Tabela '{TABLE_NAME}' não existe em {DB_PATH}. Crie o schema SQL antes da carga.")
    return [coluna[1] for coluna in colunas]


def preparar_dataframe(df: pd.DataFrame, colunas_tabela: list[str]) -> pd.DataFrame:
    df = df.copy()
    if "alerta_gerado" in df.columns:
        df["alerta_gerado"] = df["alerta_gerado"].astype(bool).astype(int)

    colunas_geradas_banco = {"data_ingestao"}
    if "id_registro" not in colunas_tabela:
        colunas_geradas_banco.add("id_registro")

    colunas_insert = [col for col in colunas_tabela if col in df.columns and col not in colunas_geradas_banco]
    return df[colunas_insert]


def carregar_dados() -> int:
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {FEATURES_PATH}. Rode feature_engineering.py primeiro.")

    df = pd.read_csv(FEATURES_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        carregar_equipamentos(conn, df)
        colunas_tabela = obter_colunas_tabela(conn)
        dados = preparar_dataframe(df, colunas_tabela)
        placeholders = ", ".join(["?"] * len(dados.columns))
        colunas_sql = ", ".join(dados.columns)
        sql = f"INSERT OR IGNORE INTO {TABLE_NAME} ({colunas_sql}) VALUES ({placeholders})"
        antes = conn.total_changes
        conn.executemany(sql, dados.itertuples(index=False, name=None))
        conn.commit()
        return conn.total_changes - antes


def main() -> None:
    inseridos = carregar_dados()
    print(f"{inseridos} registros inseridos em {DB_PATH}:{TABLE_NAME}")


if __name__ == "__main__":
    main()
