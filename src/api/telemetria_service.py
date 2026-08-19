from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import sqlite3

from ml.predictor import RiskPredictor
from ml.recomendacao import recomendar


SOLO_ENCODER = {"Arenoso": 0, "Misto": 1, "Argiloso": 2}
OPERACAO_ENCODER = {"Transporte": 0, "Campo": 1}
FAIXA_ENCODER = {"Baixo": 0, "Médio": 1, "Alto": 2, "Crítico": 3}


def _faixa_proximidade(valor: int) -> str:
    if valor < 50:
        return "Crítico"
    if valor < 200:
        return "Alto"
    if valor < 500:
        return "Médio"
    return "Baixo"


def _calcular_features(dados: dict) -> dict:
    """Adiciona as features derivadas esperadas pelo modelo."""
    row = dict(dados)
    row["tipo_solo_encoded"] = SOLO_ENCODER[row["tipo_solo"]]
    row["tipo_operacao_encoded"] = OPERACAO_ENCODER[row["tipo_operacao"]]
    faixa = _faixa_proximidade(row["proximidade_agua_m"])
    row["faixa_proximidade_agua"] = faixa
    row["faixa_proximidade_encoded"] = FAIXA_ENCODER[faixa]
    row["indice_desgaste"] = row["horas_uso_equipamento"] / max(row["dias_ultima_manutencao"], 1)
    row["risco_solo"] = (
        row["umidade_solo_pct"] * row["tipo_solo_encoded"]
    ) / max(row["declividade_graus"], 0.1)
    row["risco_atolamento"] = (
        row["faixa_proximidade_encoded"] * 25
        + row["umidade_solo_pct"] * 0.35
        + row["precipitacao_mm"] * 0.25
        + row["tipo_solo_encoded"] * 8
    )
    row["risco_operacional"] = (
        row["velocidade_operacao_kmh"] * (3 if row["tipo_operacao"] == "Campo" else 0.6)
        + row["carga_pct"] * 0.3
        + row["declividade_graus"] * 2
        + max(0, 1000 - row["visibilidade_m"]) * 0.02
    )
    row["risco_manutencao"] = (
        row["horas_uso_equipamento"] / 120
        + row["dias_ultima_manutencao"] * 0.35
        + row["historico_incidentes"] * 9
    )
    return row


def _score_regra(row: dict) -> int:
    """Calcula o score de risco pela regra heurística (mesma lógica do generate_dataset)."""
    score = 0
    score += max(0, 50 - row["proximidade_agua_m"] / 10)
    score += row["umidade_solo_pct"] * 0.25
    score += row["precipitacao_mm"] * 0.35
    score += row["tipo_solo_encoded"] * 5
    score += row["declividade_graus"] * 1.5
    score += row["velocidade_operacao_kmh"] * (1.2 if row["tipo_operacao"] == "Campo" else 0.2)
    score += row["carga_pct"] * 0.15
    score += row["historico_incidentes"] * 7
    score += max(0, row["dias_ultima_manutencao"] - 30) * 0.3
    score += max(0, row["horas_uso_equipamento"] - 3000) / 200
    score += max(0, 1000 - row["visibilidade_m"]) * 0.01
    return int(min(100, max(0, score)))


def _classificar_risco(score: int) -> str:
    if score <= 25:
        return "Baixo"
    if score <= 50:
        return "Médio"
    if score <= 75:
        return "Alto"
    return "Crítico"


def _inserir_telemetria(conn: sqlite3.Connection, dados: dict) -> int:
    colunas = [
        "id_equipamento",
        "data_hora",
        "latitude",
        "longitude",
        "tipo_operacao",
        "proximidade_agua_m",
        "precipitacao_mm",
        "umidade_solo_pct",
        "tipo_solo",
        "declividade_graus",
        "temperatura_c",
        "velocidade_vento_kmh",
        "visibilidade_m",
        "horas_uso_equipamento",
        "dias_ultima_manutencao",
        "velocidade_operacao_kmh",
        "carga_pct",
        "nivel_combustivel_pct",
        "historico_incidentes",
        "score_risco",
        "nivel_risco",
        "alerta_gerado",
        "tipo_solo_encoded",
        "tipo_operacao_encoded",
        "faixa_proximidade_agua",
        "faixa_proximidade_encoded",
        "indice_desgaste",
        "risco_solo",
        "risco_atolamento",
        "risco_operacional",
        "risco_manutencao",
    ]
    valores = [dados.get(col) for col in colunas]
    placeholders = ", ".join(["?"] * len(colunas))
    sql = f"INSERT INTO telemetria ({', '.join(colunas)}) VALUES ({placeholders})"
    cursor = conn.cursor()
    cursor.execute(sql, valores)
    return cursor.lastrowid


def _inserir_score_modelo(conn: sqlite3.Connection, pred: dict) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO scores_modelo
            (id_registro, id_equipamento, data_hora_predicao, score_risco_predito,
             nivel_risco_predito, alerta_predito, modelo_utilizado, probabilidades, fatores_principais)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pred["id_registro"],
            pred["id_equipamento"],
            datetime.now().isoformat(),
            pred["score_risco_predito"],
            pred["nivel_risco_predito"],
            pred["alerta_predito"],
            pred["modelo_utilizado"],
            pred["probabilidades"],
            pred["fatores_principais"],
        ),
    )


def _inserir_alerta(conn: sqlite3.Connection, id_registro: int, id_equipamento: str, nivel: str, score: int) -> None:
    if nivel not in ("Alto", "Crítico"):
        return
    mensagem = recomendar(nivel)
    tipo_alerta = "Crítico" if nivel == "Crítico" else "Preventivo"
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO alertas (id_registro, id_equipamento, nivel_risco, score_risco, mensagem, tipo_alerta)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (id_registro, id_equipamento, nivel, score, mensagem, tipo_alerta),
    )


def processar_telemetria(conn: sqlite3.Connection, dados: dict, predictor: RiskPredictor) -> dict:
    """Fluxo completo: insere telemetria, calcula score, prediz e registra alerta."""
    row = _calcular_features(dados)
    row["data_hora"] = datetime.now().isoformat()
    row["score_risco"] = _score_regra(row)
    row["nivel_risco"] = _classificar_risco(row["score_risco"])
    row["alerta_gerado"] = int(row["nivel_risco"] in ("Alto", "Crítico"))

    id_registro = _inserir_telemetria(conn, row)
    row["id_registro"] = id_registro

    df = pd.DataFrame([row])
    pred_df = predictor.predict(df)
    pred = pred_df.iloc[0].to_dict()
    pred["id_registro"] = id_registro
    pred["id_equipamento"] = row["id_equipamento"]

    _inserir_score_modelo(conn, pred)
    _inserir_alerta(conn, id_registro, row["id_equipamento"], pred["nivel_risco_predito"], pred["score_risco_predito"])

    fatores = json.loads(pred["fatores_principais"])
    return {
        "id_registro": id_registro,
        "id_equipamento": row["id_equipamento"],
        "score_risco": row["score_risco"],
        "nivel_risco": row["nivel_risco"],
        "alerta_gerado": bool(row["alerta_gerado"]),
        "score_risco_predito": pred["score_risco_predito"],
        "nivel_risco_predito": pred["nivel_risco_predito"],
        "alerta_predito": bool(pred["alerta_predito"]),
        "recomendacao": recomendar(pred["nivel_risco_predito"], fatores),
        "fatores_principais": fatores,
        "data_hora": row["data_hora"],
    }
