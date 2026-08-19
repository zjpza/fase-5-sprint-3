from __future__ import annotations

from typing import Annotated

import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.database import get_db
from api.schemas import (
    AlertaResponse,
    EquipamentoResponse,
    LoginInput,
    TelemetriaInput,
    TelemetriaResponse,
    TokenResponse,
)
from api.telemetria_service import processar_telemetria
from ml.predictor import RiskPredictor
from security.audit_logger import log
from security.auth import authenticate, create_access_token, get_current_user

router = APIRouter(prefix="/api/v1")


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginInput,
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    user = authenticate(payload.email, payload.senha)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    log(
        db,
        id_usuario=user["id_usuario"],
        acao="login",
        recurso="/api/v1/login",
        detalhes=f"Login realizado por {user['nome']}",
        ip_origem=_get_client_ip(request),
    )
    return {"access_token": create_access_token(user), "token_type": "bearer"}


@router.get("/equipamentos", response_model=list[EquipamentoResponse])
def listar_equipamentos(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    request: Request,
    user: dict = Depends(get_current_user),
):
    log(
        db,
        id_usuario=user["id_usuario"],
        acao="listar_equipamentos",
        recurso="/api/v1/equipamentos",
        ip_origem=_get_client_ip(request),
    )
    cursor = db.execute("SELECT * FROM equipamentos")
    return [dict(row) for row in cursor.fetchall()]


@router.get("/equipamentos/{id_equipamento}/risco")
def risco_equipamento(
    id_equipamento: str,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    request: Request,
    user: dict = Depends(get_current_user),
):
    if user["role"] == "Operador" and user.get("id_equipamento_acesso") != id_equipamento:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a este equipamento")

    cursor = db.execute(
        """
        SELECT t.*, sm.nivel_risco_predito, sm.score_risco_predito
        FROM telemetria t
        LEFT JOIN scores_modelo sm ON t.id_registro = sm.id_registro
        WHERE t.id_equipamento = ?
        ORDER BY t.data_hora DESC
        LIMIT 1
        """,
        (id_equipamento,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipamento não encontrado ou sem telemetria")

    log(
        db,
        id_usuario=user["id_usuario"],
        acao="consultar_risco",
        recurso=f"/api/v1/equipamentos/{id_equipamento}/risco",
        id_equipamento=id_equipamento,
        ip_origem=_get_client_ip(request),
    )
    return dict(row)


@router.get("/alertas", response_model=list[AlertaResponse])
def listar_alertas(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    request: Request,
    user: dict = Depends(get_current_user),
):
    if user["role"] == "Operador":
        id_equipamento = user.get("id_equipamento_acesso")
        cursor = db.execute(
            "SELECT * FROM alertas WHERE id_equipamento = ? ORDER BY data_hora_alerta DESC",
            (id_equipamento,),
        )
    else:
        cursor = db.execute("SELECT * FROM alertas ORDER BY data_hora_alerta DESC LIMIT 100")

    log(
        db,
        id_usuario=user["id_usuario"],
        acao="listar_alertas",
        recurso="/api/v1/alertas",
        ip_origem=_get_client_ip(request),
    )
    return [dict(row) for row in cursor.fetchall()]


@router.post("/telemetria", response_model=TelemetriaResponse, status_code=status.HTTP_201_CREATED)
def receber_telemetria(
    payload: TelemetriaInput,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    request: Request,
    user: dict = Depends(get_current_user),
):
    if user["role"] == "Operador" and user.get("id_equipamento_acesso") != payload.id_equipamento:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operador não autorizado para este equipamento")

    predictor = RiskPredictor()
    try:
        resultado = processar_telemetria(db, payload.model_dump(), predictor)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao processar telemetria: {exc}")

    log(
        db,
        id_usuario=user["id_usuario"],
        acao="receber_telemetria",
        recurso="/api/v1/telemetria",
        id_equipamento=payload.id_equipamento,
        id_registro=resultado["id_registro"],
        detalhes=f"score_regra={resultado['score_risco']}; predito={resultado['nivel_risco_predito']}",
        ip_origem=_get_client_ip(request),
    )
    return resultado
